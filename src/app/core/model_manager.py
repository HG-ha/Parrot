import os
import subprocess
import threading
import aiohttp
import asyncio
import py7zr
import app.core.mlog as mlog
from py7zr.callbacks import ExtractCallback

class ModelExtractCallback(ExtractCallback):
    """模型解压进度回调类"""
    def __init__(self, progress_callback):
        self.progress_callback = progress_callback
        self.total_files = 0
        self.current_file = 0
        
    def report_start(self, filename, filesize):
        """开始解压文件时的回调"""
        self.current_file += 1
        if self.progress_callback:
            self.progress_callback(self.current_file, self.total_files, f"正在解压({self.current_file}/{self.total_files}): {filename}")
    
    def report_end(self, filename, filesize):
        """文件解压完成时的回调"""
        if self.progress_callback:
            self.progress_callback(self.current_file, self.total_files, f"完成解压({self.current_file}/{self.total_files}): {filename}")
    
    def report_warning(self, message):
        """解压警告时的回调"""
        if self.progress_callback:
            # 忽略特定的压缩算法警告
            if "unsupported compression algorythm" not in str(message):
                self.progress_callback(-1, -1, f"警告: {message}")
        
    def report_start_preparation(self):
        """开始准备解压时的回调"""
        if self.progress_callback:
            self.progress_callback(-1, -1, "正在准备解压模型文件...")
    
    def report_postprocess(self):
        """解压后处理时的回调"""
        if self.progress_callback:
            self.progress_callback(-1, -1, "解压完成，正在清理...")
        
    def report_update(self, size):
        """解压进度更新的回调"""
        pass

    def init_total_files(self, total):
        """初始化总文件数"""
        self.total_files = total
        self.current_file = 0

class ModelManager:
    """
    模型管理类，负责模型的启动和停止
    """
    def __init__(self):
        """初始化模型管理器"""
        self.state = {
            "process": None,  # 保存运行中的模型进程
            "running": False,  # 模型运行状态
            "output": [],     # 捕获的输出
            "max_output_lines": 200,  # 最大输出行数
            "output_lock": threading.Lock(),  # 输出锁
            "model_path": os.path.join(os.getcwd(), "cosyvoice_api"),  # 模型路径
            "starting": False,  # 添加启动中状态
            "api_url": None,  # 添加 API URL 存储
        }
        self.root_dir = os.getcwd()
        self.model_url = "https://dlink.host/1drv/aHR0cHM6Ly8xZHJ2Lm1zL3UvYy8yOWVhYmExOWVkNzdkNjRhL0VXYThPeVhPTGIxS29DWVgtNmxKSGVVQkhLaUk0VnpLbW5SeUZmOGsweXVtWVE/ZT1tbGFGemg"
    
    def is_model_path_exists(self):
        """
        检查模型路径是否存在
        
        Returns:
            bool: 路径是否存在
        """
        return os.path.exists(self.state["model_path"])
    
    def run_model(self, host='127.0.0.1', port='8000', on_output=None, update_status=None):
        """
        运行模型
        
        Args:
            host: 主机地址
            port: 端口号
            on_output: 输出回调函数
        
        Returns:
            tuple: (成功状态, 错误消息)
        """
        try:
            model_path = self.state["model_path"]
            if not os.path.exists(model_path):
                error_msg = f"模型路径不存在: {model_path}"
                mlog.error(error_msg)
                return False, "MODEL_NOT_FOUND"
            
            # 使用cosyvoice_api目录下的Python解释器
            python_exe = os.path.join(model_path, "python.exe")
            if not os.path.exists(python_exe):
                error_msg = f"Python解释器不存在: {python_exe}"
                mlog.error(error_msg)
                return False, "PYTHON_NOT_FOUND"
            
            # 构建命令并启动进程
            cmd = [
                python_exe,  # 使用cosyvoice_api目录下的Python解释器
                "fastapi_app.py",
                "--host", host,
                "--port", port
            ]

            env = os.environ.copy()
            env['PYTHONHOME'] = model_path  # 设置Python Home为模型目录
            env['PYTHONPATH'] = os.path.join(model_path, 'Lib', 'site-packages')

            # 清空之前的输出
            with self.state["output_lock"]:
                self.state["output"] = []
            
            # 添加 Windows 特定的启动标志
            startupinfo = None
            if os.name == 'nt':  # Windows 系统
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # 修改进程创建部分，添加编码处理
            process = subprocess.Popen(
                cmd,
                cwd=model_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',  # 添加错误处理策略
                env=env,
                startupinfo=startupinfo  # 添加这行来隐藏控制台窗口
            )
            
            self.state["process"] = process
            self.state["running"] = False
            self.state["starting"] = True  # 设置启动中状态
            
            # 保存API URL用于健康检查
            self.state["api_url"] = f"http://{host}:{port}"
            
            # 启动线程捕获输出
            threading.Thread(
                target=self._capture_output,
                args=(on_output,update_status),
                daemon=True
            ).start()
            return True, None
        except Exception as e:
            error_msg = f"启动模型失败: {str(e)}"
            mlog.error(error_msg)
            return False, error_msg
    
    async def _check_model_health(self):
        """检查模型是否真正启动成功"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.state['api_url']}/model_status") as response:
                    return response.status == 200
        except Exception as e:
            mlog.error(f"模型健康检查失败: {str(e)}")
            return False

    async def _wait_for_model_ready_async(self, max_retries=30, delay=1):
        """异步等待模型准备就绪
        
        Args:
            max_retries: 最大重试次数
            delay: 每次重试间隔(秒)
        
        Returns:
            bool: 是否成功启动
        """
        for _ in range(max_retries):
            if await self._check_model_health():
                return True
            await asyncio.sleep(delay)
        return False
    
    def _wait_for_model_ready(self, max_retries=30, delay=1):
        """等待模型准备就绪
        
        Args:
            max_retries: 最大重试次数
            delay: 每次重试间隔(秒)
        
        Returns:
            bool: 是否成功启动
        """
        # 使用事件循环运行异步方法
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(self._wait_for_model_ready_async(max_retries, delay))
        loop.close()
        return result
    
    def _capture_output(self, on_output=None, update_status=None):
        """
        捕获模型输出
        
        Args:
            on_output: 输出回调函数
            update_status: 状态更新回调函数
        """
        process = self.state["process"]
        if not process:
            return
        
        try:
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                
                try:
                    # 添加输出行到缓存
                    with self.state["output_lock"]:
                        # 过滤掉不可打印字符
                        cleaned_line = ''.join(char for char in line.strip() if char.isprintable())
                        self.state["output"].append(cleaned_line)
                        
                        # 限制输出行数
                        if len(self.state["output"]) > self.state["max_output_lines"]:
                            self.state["output"] = self.state["output"][-self.state["max_output_lines"]:]
                        
                        # 如果有回调函数，确保在主线程中调用
                        if on_output:
                            output_text = "\n".join(self.state["output"])
                            try:
                                on_output(output_text)
                            except Exception as callback_error:
                                pass
                
                except Exception as line_error:
                    mlog.error(f"处理输出行时出错: {str(line_error)}")
                    continue
                
                # 检测启动信号并进行健康检查
                if "Uvicorn running on" in line:
                    # 启动健康检查线程
                    def health_check():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        if loop.run_until_complete(self._wait_for_model_ready_async()):
                            self.state["starting"] = False
                            self.state["running"] = True

                            # 确认加载完成后更新状态
                            if update_status is not None:
                                update_status(True)
                        else:
                            mlog.error("模型启动超时")
                            self.stop_model()  # 启动失败时停止模型
                        loop.close()
                    
                    threading.Thread(
                        target=health_check,
                        daemon=True
                    ).start()
                
                # 确保回调在状态更新后执行
                with self.state["output_lock"]:
                    if on_output:
                        output_text = "\n".join(self.state["output"])
                        try:
                            on_output(output_text)
                        except Exception as callback_error:
                            # mlog.error(f"输出回调执行失败: {str(callback_error)}")
                            pass
                    
        except Exception as e:
            mlog.error(f"捕获模型输出失败: {str(e)}")
        finally:
            # 进程结束后更新状态
            if process.poll() is not None:
                self.state["starting"] = False
                self.state["running"] = False
                # 确保最后一次输出能够显示
                if on_output:
                    try:
                        output_text = "\n".join(self.state["output"])
                        on_output(output_text)
                    except Exception as final_error:
                        mlog.error(f"最终输出回调执行失败: {str(final_error)}")
    
    def stop_model(self):
        """
        停止模型
        
        Returns:
            bool: 停止是否成功
        """
        if self.state["process"] and (self.state["running"] or self.state["starting"]):
            try:
                # 在Windows上终止进程及其子进程
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.state["process"].pid)],stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                else:
                    self.state["process"].terminate()
                    self.state["process"].wait(timeout=5)
                
                self.state["starting"] = False
                self.state["running"] = False
                self.state["process"] = None
                return True
            except Exception as e:
                mlog.error(f"停止模型失败: {str(e)}")
                return False
        return True  # 如果没有运行中的模型，也返回成功
    
    def is_running(self):
        """
        检查模型是否正在运行
        
        Returns:
            bool: 是否正在运行
        """
        return self.state["running"]
    
    def is_starting(self):
        """
        检查模型是否正在启动中
        
        Returns:
            bool: 是否正在启动
        """
        return self.state["starting"]
    
    def get_output(self):
        """
        获取当前模型输出
        
        Returns:
            str: 所有输出行组合的文本
        """
        with self.state["output_lock"]:
            return "\n".join(self.state["output"])
    
    async def download_model(self, progress_callback=None):
        """
        下载模型文件
        
        Args:
            progress_callback: 进度回调函数，接收两个参数：当前大小和总大小
            
        Returns:
            tuple: (是否成功, 错误信息)
        """
        try:
            # 创建临时文件路径
            temp_zip = os.path.join(self.root_dir, "cosyvoice_api.7z")
            # 确保cosyvoice_api目录存在
            model_path = os.path.join(self.root_dir, "cosyvoice_api")
            os.makedirs(model_path, exist_ok=True)

            # 检查文件是否已存在
            if os.path.exists(temp_zip):
                if progress_callback:
                    progress_callback(-1, -1, "模型文件已存在，开始解压...")
            else:
                # 执行下载流程
                timeout = aiohttp.ClientTimeout(total=36000)  # 设置10小时超时
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    try:
                        if progress_callback:
                            progress_callback(-1, -1, "正在连接下载服务器...")
                        
                        async with session.get(self.model_url) as response:
                            if response.status != 200:
                                error_msg = f"下载失败: 状态码 {response.status}"
                                mlog.error(error_msg)
                                return False, error_msg

                            total_size = int(response.headers.get('content-length', 0))
                            chunk_size = 8192
                            current_size = 0

                            if progress_callback:
                                progress_callback(0, total_size, "开始下载模型文件...")

                            with open(temp_zip, 'wb') as f:
                                async for chunk in response.content.iter_chunked(chunk_size):
                                    if chunk:
                                        f.write(chunk)
                                        current_size += len(chunk)
                                        if progress_callback:
                                            progress_callback(current_size, total_size, "正在下载模型文件...")
                    except aiohttp.ClientError as e:
                        error_msg = f"网络错误: {str(e)}"
                        mlog.error(error_msg)
                        return False, error_msg
                    except asyncio.TimeoutError:
                        error_msg = "下载超时，请检查网络连接"
                        mlog.error(error_msg)
                        return False, error_msg
            
            # 解压文件
            try:
                if progress_callback:
                    progress_callback(-1, -1, "正在打开压缩文件...")

                with py7zr.SevenZipFile(temp_zip, 'r') as archive:
                    # 获取压缩包中的文件列表时忽略错误
                    try:
                        all_files = archive.getnames()
                    except Exception as e:
                        if "unsupported compression algorythm" not in str(e):
                            raise e
                        all_files = []  # 如果获取失败，使用空列表
                    
                    total_files = len(all_files) or 100  # 如果获取失败，使用默认值
                    
                    # 创建解压回调实例
                    callback = ModelExtractCallback(progress_callback)
                    callback.init_total_files(total_files)
                    
                    if progress_callback:
                        progress_callback(-1, -1, f"开始解压，共 {total_files} 个文件...")
                    
                    # 开始解压，忽略特定警告
                    try:
                        archive.extractall(path=model_path, callback=callback)
                    except Exception as e:
                        if "unsupported compression algorythm" not in str(e):
                            raise e
                
                if progress_callback:
                    progress_callback(-1, -1, "解压完成，正在清理临时文件...")
                
                # 删除临时7z文件
                # os.remove(temp_zip)
                
                if progress_callback:
                    progress_callback(-1, -1, "模型文件准备就绪！")
                
                return True, None
                
            except py7zr.Bad7zFile:
                error_msg = "下载的文件已损坏，请重试"
                mlog.error(error_msg)
                # 删除损坏的文件
                if os.path.exists(temp_zip):
                    os.remove(temp_zip)
                return False, error_msg
            except Exception as e:
                error_msg = f"解压模型文件失败: {str(e)}"
                mlog.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"下载模型文件失败: {str(e)}"
            mlog.error(error_msg)
            return False, error_msg
            
    def check_model_exists(self):
        """
        检查模型文件是否存在
        
        Returns:
            bool: 模型文件是否存在
        """
        model_path = os.path.join(self.root_dir, "cosyvoice_api")
        return os.path.exists(model_path)
