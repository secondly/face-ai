@echo off
echo 🎭 启动AI换脸工具...
echo =====================================

cd /d "."

if not exist "venv" (
    echo ❌ 虚拟环境不存在，请先运行 setup_venv.py
    pause
    exit /b 1
)

echo 🔧 激活虚拟环境...
call "venv\Scripts\activate.bat"

echo 🚀 启动AI换脸工具...
"venv\Scripts\python.exe" main_pyqt.py

if errorlevel 1 (
    echo ❌ 程序运行出错
    pause
)
