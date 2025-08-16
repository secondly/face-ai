@echo off
echo 🎭 AI换脸工具 - 快速启动
echo ================================

echo 📋 正在激活CUDA环境...
call conda deactivate 2>nul
call conda activate face-ai-cuda11

if errorlevel 1 (
    echo ❌ 错误：无法激活face-ai-cuda11环境
    echo.
    echo 💡 请先创建CUDA环境，参考：CUDA虚拟环境使用说明.md
    echo.
    pause
    exit /b 1
)

echo ✅ 环境激活成功
echo.
echo 🔍 检查环境状态...
echo 当前Python路径:
where python
echo.
echo 当前环境:
conda info --envs | findstr "*"
echo.
echo 🚀 正在启动AI换脸工具...
python main_pyqt.py

if errorlevel 1 (
    echo.
    echo ❌ 程序启动失败
    echo 💡 请检查依赖是否正确安装
    pause
)
