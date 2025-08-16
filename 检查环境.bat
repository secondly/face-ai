@echo off
echo 🔍 环境检查工具
echo ================================

echo 📋 当前conda环境:
conda info --envs | findstr "*"

echo.
echo 📋 可用的conda环境:
conda env list

echo.
echo 📋 如果要激活CUDA环境:
echo conda activate face-ai-cuda11

echo.
echo 📋 如果要启动AI换脸工具:
echo 双击 "启动AI换脸.bat"

pause
