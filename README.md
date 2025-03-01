# CosyVoice2.0-0.5B 角色管理系统

[English](./README_en.md) | 简体中文

基于 CosyVoice2-0.5B 的多角色语音克隆项目。

> 模型运行要求：至少 6GB 可用 RAM 或 GPU 内存， 至少10GB存储空间

## 主要功能

- 支持本地音频文件或 URL 直接克隆
- 预设角色一键切换音色
- 历史记录参数快速复用
- 支持模型自动加载

## 使用指南

### 开箱即用
1. 在Release中下载对应平台版本
2. 模型下载二选一
    1. 手动下载模型文件
        1. 下载地址
            - [百度网盘](https://pan.baidu.com/s/1731fksU1zH0YPAU1Bfgx-Q?pwd=y67e) 提取码: y67e
            - [Onedrive](https://1drv.ms/u/c/29eaba19ed77d64a/EQVNg3H2_p1OrGo3sXeIgIoBXCEphc55pq9ZvyxUMTAIBw?e=UpIF28)
            - [Onedrive国内下载地址](https://dlink.host/1drv/aHR0cHM6Ly8xZHJ2Lm1zL3UvYy8yOWVhYmExOWVkNzdkNjRhL0VXYThPeVhPTGIxS29DWVgtNmxKSGVVQkhLaUk0VnpLbW5SeUZmOGsweXVtWVE/ZT1tbGFGemg)
        2. 运行程序后点击 `设置` - `模型目录`，将模型文件解压至此

    2. 自动下载模型文件（偶尔较慢）
        > 启动后，点击设置界面中的“运行模型”按钮，自动下载模型文件

4. 双击Parrot.exe运行

### 开发环境

1. **克隆项目**
    ```bash
    git clone --recursive https://github.com/HG-ha/CosyVoice_Role_management.git
    ```

2. **安装依赖**
   - 安装 [Miniconda](https://docs.anaconda.com/miniconda/install/#quick-command-line-install)
   - 配置环境：
        ```bash
        # 创建并激活环境
        conda create -n cosyvoice -y python=3.10
        conda activate cosyvoice

        # 安装其他依赖
        pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com
        ```
3. **运行**
    ```bash
    # 在桌面运行
    flet run

    # 在浏览器中运行
    flet run -w --host 127.0.0.1 -p 8000
    ```

### 模型获取

可在启动后通过设置界面下载，或使用以下代码：

```python
from modelscope import snapshot_download
snapshot_download('iic/CosyVoice2-0.5B', local_dir='pretrained_models/CosyVoice2-0.5B')
```

## 界面展示

### 主页面
<div align="center">
  <img src="./asset/Home.png" alt="主页界面" width="800"/>
  <p><em>主页界面 - 提供语音克隆核心功能和角色切换</em></p>
</div>

### 历史记录
<div align="center">
  <img src="./asset/history.png" alt="历史记录" width="800"/>
  <p><em>历史记录页面 - 查看和复用以往的语音克隆参数</em></p>
</div>

### 角色管理
<div align="center">
  <img src="./asset/role.png" alt="角色管理" width="800"/>
  <p><em>角色管理界面 - 添加、编辑和管理预设角色</em></p>
</div>

### 系统配置
<div align="center">
  <img src="./asset/setting.png" alt="系统设置" width="800"/>
  <p><em>设置界面 - 调整系统参数和模型配置</em></p>
</div>
