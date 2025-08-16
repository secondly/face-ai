# CUDA版本管理指南

## 🎯 问题描述

你的系统当前安装了CUDA 12.3，其他项目需要使用这个版本，但AI换脸项目需要CUDA 11.8才能与ONNX Runtime 1.17.1兼容。

## 💡 解决方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **conda环境隔离** | 完美隔离，GPU加速可用 | 需要额外磁盘空间 | 经常使用AI换脸 |
| **Docker容器** | 完全隔离，可移植 | 配置复杂，需要Docker | 专业开发环境 |
| **接受CPU模式** | 无需修改环境 | 速度较慢 | 偶尔使用 |
| **等待更新** | 无需操作 | 时间不确定 | 不急于使用 |

## 🚀 推荐方案：conda环境隔离

### 步骤1：创建专用环境
```bash
# 创建新环境
conda create -n face-ai-cuda11 python=3.8

# 激活环境
conda activate face-ai-cuda11

# 安装CUDA 11.8
conda install cudatoolkit=11.8 cudnn=8.2 -c conda-forge

# 安装兼容的ONNX Runtime
pip install onnxruntime-gpu==1.15.1

# 安装项目依赖
pip install -r requirements.txt
```

### 步骤2：使用方法
```bash
# 使用AI换脸项目时
conda activate face-ai-cuda11
python main_pyqt.py

# 使用其他项目时
conda activate base  # 或其他环境
# 继续使用CUDA 12.3
```

### 步骤3：验证环境
```python
# 在face-ai-cuda11环境中运行
import torch
print(f"PyTorch CUDA版本: {torch.version.cuda}")
print(f"CUDA可用: {torch.cuda.is_available()}")

import onnxruntime as ort
print(f"ONNX Runtime版本: {ort.__version__}")
print(f"可用提供者: {ort.get_available_providers()}")
```

## 🔧 自动化脚本

我已经为你创建了 `setup_cuda11_env.bat` 脚本，直接运行即可自动配置环境。

## 📋 环境管理命令

```bash
# 查看所有环境
conda env list

# 激活AI换脸环境
conda activate face-ai-cuda11

# 激活默认环境（CUDA 12.3）
conda activate base

# 删除环境（如果不需要了）
conda env remove -n face-ai-cuda11
```

## 🎯 最终效果

- **AI换脸项目**: 使用CUDA 11.8，GPU加速完全可用
- **其他项目**: 继续使用CUDA 12.3，不受影响
- **切换简单**: 只需要激活不同的conda环境

## ⚠️ 注意事项

1. **磁盘空间**: 新环境大约需要2-3GB空间
2. **环境切换**: 每次使用前记得激活正确的环境
3. **依赖管理**: 两个环境的依赖包是独立的

## 🚀 快速开始

1. 运行 `setup_cuda11_env.bat`
2. 等待安装完成
3. 激活环境: `conda activate face-ai-cuda11`
4. 启动AI换脸: `python main_pyqt.py`
5. 享受GPU加速！

这样你就可以在不影响其他项目的情况下，让AI换脸项目获得完整的GPU加速支持！
