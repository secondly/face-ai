# CUDA 虚拟环境使用说明

## 🎯 新方案：在项目内创建 CUDA 虚拟环境

✅ **推荐方案**: 在项目根目录创建独立的 CUDA 虚拟环境
🎯 **目标**: 用于离线打包，避免 C 盘依赖

## 📋 在项目内创建 CUDA 环境步骤（简化版）

### 第一步：进入项目根目录

```bash
# 打开PowerShell或命令提示符
cd G:\tok\face-ai

# 确认当前位置（应该看到main_pyqt.py和requirements.txt等文件）
dir
```

### 第二步：创建项目内 CUDA 环境

```bash
# 重要：使用--prefix在项目内创建环境
conda create --prefix ./cuda_env python=3.8 -y
```

### 第三步：激活环境并安装 CUDA 工具包

```bash
# 激活项目内的环境
conda activate ./cuda_env

# 安装CUDA工具包
conda install cudatoolkit=11.8 cudnn=8.2 -c conda-forge -y
```

### 第四步：一键安装所有 AI 依赖

```bash
# 使用requirements.txt一键安装所有依赖
pip install -r requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org

# 安装CUDA版本的PyTorch（覆盖CPU版本）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 第五步：验证安装

```bash
# 检查CUDA是否可用
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"

# 检查ONNX Runtime GPU
python -c "import onnxruntime as ort; print('GPU providers:', [p for p in ort.get_available_providers() if 'CUDA' in p])"

# 检查其他库
python -c "import cv2, numpy, insightface; print('All libraries imported successfully')"
```

## 🚀 完整命令（复制粘贴版）

```bash
# 一次性执行所有命令
cd G:\tok\face-ai
conda create --prefix ./cuda_env python=3.8 -y
conda activate ./cuda_env
conda install cudatoolkit=11.8 cudnn=8.2 -c conda-forge -y
pip install -r requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

## 🚀 日常使用方法

### 启动 AI 换脸工具

```bash
# 方法1：激活环境后运行
conda activate ./cuda_env
python main_pyqt.py

# 方法2：直接使用环境中的Python
./cuda_env/python.exe main_pyqt.py
```

### 切换回原环境

```bash
conda deactivate
```

## 🔧 环境管理

### 查看项目环境信息

```bash
# 查看环境大小
# PowerShell:
(Get-ChildItem cuda_env -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB

# 查看已安装的包
conda list --prefix ./cuda_env
```

### 删除环境（如果需要重建）

```bash
# 删除整个环境目录
rmdir /s cuda_env
# 或者
Remove-Item cuda_env -Recurse -Force
```

### 检查环境位置

```bash
# 确认环境在项目内
dir cuda_env
# 应该看到：python.exe, Scripts/, Lib/ 等
```

## ✅ 验证 GPU 加速

运行程序后，在启动检测界面应该看到：

- ✅ CUDA 版本兼容
- ✅ GPU 加速可用
- ✅ 未发现问题

## 📊 环境信息

- **环境位置**: G:\tok\face-ai\cuda_env\
- **Python 版本**: 3.8
- **CUDA 版本**: 11.8
- **cuDNN 版本**: 8.2
- **ONNX Runtime**: 1.15.1 (GPU 版本)
- **PyTorch**: CUDA 11.8 版本
- **环境大小**: 约 2-4GB

## 🎯 预期效果

使用这个项目内环境后：

- ✅ GPU 加速正常工作
- ✅ 处理速度提升 2-3 倍
- ✅ 完全独立，不影响系统环境
- ✅ 可直接用于离线打包
- ✅ 无需 C 盘依赖

## 🔧 GPU 内存管理

### 自动内存清理

- **处理完成后**: 程序自动清理 GPU 内存
- **程序退出时**: 强制释放所有 GPU 资源
- **内存监控**: 实时监控 GPU 内存使用情况

### 手动清理方法

如果发现 GPU 内存没有释放：

1. **完成当前处理**: 等待视频处理完成
2. **关闭程序**: 完全退出 AI 换脸工具
3. **重新启动**: 使用启动脚本重新打开

### GPU 使用率优化

- **并行处理**: 已优化 ONNX Runtime 会话配置
- **内存模式**: 启用内存模式优化
- **线程配置**: 自动使用所有可用 CPU 线程

## 🎯 用于离线打包

### 构建离线安装包

创建环境后，可以直接用于构建离线安装包：

```bash
# 进入installer目录
cd installer

# 运行构建脚本（会自动检测项目内的cuda_env）
powershell -ExecutionPolicy Bypass -File build_offline_package.ps1
```

### 环境复制

构建脚本会自动：

- ✅ 检测 `G:\tok\face-ai\cuda_env\` 目录
- ✅ 复制完整环境到离线包
- ✅ 生成包含 CUDA 支持的安装器

## ⚠️ 注意事项

1. **使用--prefix 创建**: 必须使用 `conda create --prefix ./cuda_env` 而不是 `-n`
2. **激活环境**: `conda activate ./cuda_env` 或直接使用 `./cuda_env/python.exe`
3. **环境隔离**: 完全独立，不影响系统其他环境
4. **磁盘空间**: 环境约占用 2-4GB 空间
5. **GPU 内存**: 处理大视频时建议关闭其他 GPU 应用
6. **离线打包**: 环境创建完成后即可用于构建离线安装包

---

**这个方案创建项目内的 CUDA 环境，完美支持离线打包，无需 C 盘依赖！**
