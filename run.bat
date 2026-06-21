@echo off
chcp 65001 >nul
title 截图工具

echo ========================================
echo          截图工具 v2.0
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查并安装依赖
echo [1/2] 检查依赖库...
pip install -r "%~dp0requirements.txt" -q

echo [2/2] 启动截图工具...
echo.
echo 提示: 按 Ctrl+Shift+S 截图，或点击浮动窗口的"截图"按钮
echo.

python "%~dp0screenshot_tool.py"

pause
