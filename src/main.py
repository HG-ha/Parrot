import flet as ft
from app.app_controller import CosyVoiceApp

# 应用名
APP_NAME = "Parrot"
PACKAGE_NAME = "com.parrot.parrot"

# Flet应用程序入口
def main(page: ft.Page):
    # 创建并初始化应用程序实例
    app = CosyVoiceApp(page, APP_NAME,PACKAGE_NAME)
    # 构建UI
    app.build()
    # 初始化应用
    app.initialize()

if __name__ == "__main__":
    ft.app(target=main)