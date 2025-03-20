import json
import aiohttp
import websockets
import os

class ApiManager:
    """
    API管理类，负责与API服务器通信
    """
    def __init__(self,pathmanager):
        """初始化API管理器"""
        self.path_manager = pathmanager
        self.temp_dir = self.path_manager.temp_dir
        self.history_dir = self.path_manager.history_dir
        
        # 确保目录存在
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.history_dir, exist_ok=True)
    
    async def check_connection(self, api_url):
        """
        检查API连接
        
        Args:
            api_url: API地址
        
        Returns:
            tuple: (是否连接成功, 消息)
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{api_url}/model_status") as response:
                    if response.status == 200:
                        return True, "API连接成功"
                    return False, f"API连接失败: HTTP {response.status}"
        except Exception as e:
            return False, f"API连接失败: {str(e)}"
    
    async def generate_audio(self, api_url, params, progress_callback=None):
        """
        生成音频
        
        Args:
            api_url: API地址
            params: 音频生成参数
            progress_callback: 进度回调函数
        
        Returns:
            tuple: (是否成功, 结果文件路径或错误消息)
        """
        try:
            # 使用 websockets 连接到 fastapi 服务器
            uri = f"ws://{api_url.replace('http://', '')}/ws/generate"
            async with websockets.connect(uri) as websocket:
                # 构造生成请求
                request = {
                    "type": "generate",
                    "text": params.get('text', ''),
                    "speed": params.get('speed', 1.0),
                }
                
                # 根据不同模式添加对应参数
                if params.get('mode') == "zero_shot":
                    request["speaker"] = params.get('speaker_text', '')
                elif params.get('mode') == "language_control":
                    request["instruction"] = params.get('language_control', '')
                    
                if params.get('prompt'):
                    request["prompt_speech_path"] = params.get('prompt')

                # 发送请求
                await websocket.send(json.dumps(request))
                
                # 接收进度和结果
                while True:
                    try:
                        response = await websocket.recv()
                        data = json.loads(response)
                        
                        if data.get("type") == "progress" and progress_callback:
                            progress_callback(data)
                        elif data.get("type") == "complete":
                            if data.get("success"):
                                return True, data.get("filepath", "")
                            else:
                                return False, data.get("message", "未知错误")
                        elif data.get("type") == "error":
                            return False, data.get("message", "生成错误")
                            
                    except Exception as e:
                        return False, str(e)
                        
        except Exception as e:
            return False, str(e)
    
    async def generate_audio_rest(self, api_url, params, progress_callback=None):
        """
        使用REST API生成音频（备用方法）
        
        Args:
            api_url: API地址
            params: 音频生成参数
            progress_callback: 进度回调函数
        
        Returns:
            tuple: (是否成功, 结果文件路径或错误消息)
        """
        try:
            # 准备请求数据
            endpoint = f"{api_url}/generate_audio"
            
            # 构造请求数据
            data = {
                "text": params.get('text', ''),
                "speed": params.get('speed', 1.0),
            }
            
            # 根据不同模式添加对应参数
            if params.get('mode') == "zero_shot":
                data["speaker"] = params.get('speaker_text', '')
            elif params.get('mode') == "language_control":
                data["instruction"] = params.get('language_control', '')
                
            if params.get('prompt'):
                data["prompt_speech_path"] = params.get('prompt')
                
            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("success"):
                            return True, result.get("filepath", "")
                        else:
                            return False, result.get("message", "未知错误")
                    else:
                        return False, f"API返回错误状态码: {response.status}"
                        
        except Exception as e:
            return False, str(e)