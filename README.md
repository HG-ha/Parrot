# CosyVoice2.0-0.5B 角色管理系统

[English](./README_en.md) | 简体中文

基于 CosyVoice2-0.5B 的多角色语音克隆项目。

> 运行要求：至少 4GB 可用 RAM 或 GPU 内存

## 主要功能

- 支持本地音频文件或 URL 直接克隆
- 预设角色一键切换音色
- 历史记录参数快速复用
- 支持模型自动加载

## 使用指南

### 环境配置

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

        # 安装 pynini（WeTextProcessing 依赖）
        conda install -y -c conda-forge pynini==2.1.5

        # 安装其他依赖
        pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com
        ```
3. **运行**
    ```bash
    python main.py
    ```

### 模型获取

可在启动后通过设置界面下载，或使用以下代码：

```python
from modelscope import snapshot_download
snapshot_download('iic/CosyVoice2-0.5B', local_dir='pretrained_models/CosyVoice2-0.5B')
```

## 界面展示

### 主页
![主页界面](./asset/Home.png)

### 历史记录
![历史记录](./asset/history.png)

### 角色管理
![角色管理](./asset/role.png)

### 系统设置
![系统设置](./asset/setting.png)
