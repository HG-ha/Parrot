# Parrot

English | [简体中文](./README.md)

Multi-character voice cloning project based on `CosyVoice2-0.5B` model using `flet` UI framework.

> System Requirements: Minimum 6GB available RAM or GPU memory, at least 10GB storage space

## Key Features

- Support local audio files or URL direct cloning
- One-click voice switching with preset characters
- Quick parameter reuse from history records
- Automatic model loading support

## Usage Guide

### Quick Start
1. Download the corresponding platform version from [Releases](https://github.com/HG-ha/Parrot/releases), run and extract
2. Choose one method to download the model
    - Manual download
        1. Download links
            - [Baidu Netdisk](https://pan.baidu.com/s/1731fksU1zH0YPAU1Bfgx-Q?pwd=y67e) Code: y67e
            - [Onedrive](https://1drv.ms/u/c/29eaba19ed77d64a/EQVNg3H2_p1OrGo3sXeIgIoBXCEphc55pq9ZvyxUMTAIBw?e=UpIF28)
            - [Onedrive China Mirror](https://dlink.host/1drv/aHR0cHM6Ly8xZHJ2Lm1zL3UvYy8yOWVhYmExOWVkNzdkNjRhL0VXYThPeVhPTGIxS29DWVgtNmxKSGVVQkhLaUk0VnpLbW5SeUZmOGsweXVtWVE/ZT1tbGFGemg)
        2. After running the program, click `Settings` - `Model Directory`, extract the model files here
            > Or move the downloaded files to this path, then click `Run Model` - `Auto Download`, the program will automatically extract and run the model

    - Automatic download (occasionally slow but convenient)
        > After startup, click the "Run Model" button in the settings interface to automatically download model files

3. Double click Parrot.exe to run

### Development Environment Setup

1. **Clone Project**
    ```bash
    git clone --recursive https://github.com/HG-ha/Parrot.git
    ```

2. **Install Dependencies**
   - Install [Miniconda](https://docs.anaconda.com/miniconda/install/#quick-command-line-install) (or other environment management tools)
   - Configure environment:
        ```bash
        # Create and activate environment
        conda create -n Parrot -y python=3.10
        conda activate Parrot

        # Install dependencies
        pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
        ```

3. **Run**
    ```bash
    # Run on desktop
    flet run

    # Run in browser
    flet run -w --host 127.0.0.1 -p 8000
    ```

### Cross-Platform Publishing
  1. It's recommended not to install Flutter SDK in the system as it may cause Flet compilation to become unresponsive. Flet will automatically install Flutter SDK during compilation
  2. Correctly install Flutter SDK dependencies
  3. Clone project
      ```bash
      git clone https://github.com/HG-ha/Parrot.git
      cd Parrot
      ```
  4. Install dependencies
      ```bash
      pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
      ```
  5. Compile
      - windows: `flet build windows`
      - linux: `flet build linux`
      - macos: `flet build macos`
      - android: `flet build apk`

## Interface Display

### Main Page
<div align="center">
  <img src="./assets/Home.png" alt="Main Interface" width="800"/>
  <p><em>Main Interface - Provides core voice cloning functionality and character switching</em></p>
</div>

### History Records
<div align="center">
  <img src="./assets/history.png" alt="History Records" width="800"/>
  <p><em>History Page - View and reuse previous voice cloning parameters</em></p>
</div>

### Character Management
<div align="center">
  <img src="./assets/role.png" alt="Character Management" width="800"/>
  <p><em>Character Management Interface - Add, edit, and manage preset characters</em></p>
</div>

### System Configuration
<div align="center">
  <img src="./assets/setting.png" alt="System Settings" width="800"/>
  <p><em>Settings Interface - Adjust system parameters and model configuration</em></p>
</div>
