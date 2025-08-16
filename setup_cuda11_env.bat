@echo off
echo 🎯 为AI换脸项目创建CUDA 11.8专用环境
echo ================================================

echo 📋 步骤1: 创建新的conda环境
conda create -n face-ai-cuda11 python=3.8 -y

echo 📋 步骤2: 激活环境
call conda activate face-ai-cuda11

echo 📋 步骤3: 安装CUDA 11.8工具包
conda install cudatoolkit=11.8 cudnn=8.2 -c conda-forge -y

echo 📋 步骤4: 安装兼容的ONNX Runtime
pip install onnxruntime-gpu==1.15.1

echo 📋 步骤5: 安装其他依赖
pip install -r requirements.txt

echo ✅ 环境创建完成！
echo 
echo 🚀 使用方法:
echo 1. 激活环境: conda activate face-ai-cuda11
echo 2. 运行AI换脸: python main_pyqt.py
echo 3. 切换回原环境: conda activate base
echo 
echo 💡 这样你的其他项目仍然可以使用CUDA 12.3
pause
