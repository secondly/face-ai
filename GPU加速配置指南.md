# AI换脸工具 GPU加速配置指南

## 📋 概述

GPU加速可以显著提升AI换脸的处理速度，特别是在处理高分辨率图像和长视频时。本指南将帮助您正确配置GPU加速。

## 🔍 GPU加速检测

程序启动时会自动检测您的GPU环境并显示详细信息：

```
================================================================================
🔍 GPU环境检测报告
================================================================================
💻 操作系统: Windows

🎮 NVIDIA GPU:
   ✅ 状态: 可用 (1个GPU)
   📊 GPU 1: NVIDIA GeForce RTX 3060
       💾 显存: 12288MB
       🔧 驱动版本: 531.29
       🚀 CUDA版本: 12.1

🚀 CUDA:
   ✅ 状态: 可用
   📋 版本: Cuda compilation tools, release 11.8, V11.8.89

🧠 ONNX Runtime:
   ✅ 状态: 可用 (版本 1.15.1)
   📋 可用提供者:
       ✅ CUDAExecutionProvider: NVIDIA CUDA GPU加速 (最佳性能)
       ✅ CPUExecutionProvider: CPU处理 (兼容性最佳)

🎯 推荐配置:
   📋 类型: NVIDIA CUDA GPU加速 (推荐)
   🚀 提供者: CUDAExecutionProvider
   📊 性能等级: excellent
   💡 原因: NVIDIA GPU + CUDA + CUDAExecutionProvider 完整支持

⚡ GPU加速: 启用
================================================================================
```

## 🎯 GPU加速类型

### 1. NVIDIA CUDA (推荐)
- **适用于**: NVIDIA GeForce/RTX/Quadro系列显卡
- **性能**: 最佳 (excellent)
- **要求**: NVIDIA驱动 + CUDA Toolkit + onnxruntime-gpu

### 2. DirectML (Windows通用)
- **适用于**: AMD/Intel/NVIDIA显卡 (Windows)
- **性能**: 良好 (good)
- **要求**: Windows 10+ + onnxruntime-directml

### 3. CPU模式 (兼容性最佳)
- **适用于**: 所有系统
- **性能**: 基础 (basic)
- **要求**: 仅需onnxruntime

## 🛠️ 配置步骤

### 方式一：自动配置 (推荐)

1. **运行GPU支持安装脚本**
   ```bash
   python scripts/install_gpu_support.py
   ```

2. **脚本会自动**：
   - 检测您的GPU硬件
   - 检测CUDA安装状态
   - 检测当前ONNX Runtime版本
   - 提供个性化安装建议
   - 自动安装合适的ONNX Runtime版本

### 方式二：手动配置

#### NVIDIA GPU用户

1. **安装NVIDIA驱动**
   - 访问 [NVIDIA官网](https://www.nvidia.com/drivers/)
   - 下载并安装最新驱动

2. **安装CUDA Toolkit**
   - 访问 [CUDA下载页面](https://developer.nvidia.com/cuda-downloads)
   - 下载并安装CUDA 11.8或更高版本

3. **安装GPU版本的ONNX Runtime**
   ```bash
   pip uninstall onnxruntime onnxruntime-gpu onnxruntime-directml -y
   pip install onnxruntime-gpu
   ```

#### AMD/Intel GPU用户 (Windows)

1. **安装DirectML版本的ONNX Runtime**
   ```bash
   pip uninstall onnxruntime onnxruntime-gpu onnxruntime-directml -y
   pip install onnxruntime-directml
   ```

## 🎮 界面中的GPU设置

### GPU状态显示

程序界面中的GPU选项会根据检测结果智能设置：

- **🚀 GPU加速 ✅** - GPU可用，默认启用
- **🚀 GPU加速 ❌** - GPU不可用，自动禁用
- **🚀 GPU加速 (强制CPU模式)** - 用户强制使用CPU

### 状态指示器

- **🚀 NVIDIA CUDA GPU加速** (绿色) - 最佳性能
- **⚡ DirectML GPU加速** (蓝色) - 良好性能  
- **🔧 CPU处理模式** (黄色) - 基础性能
- **❌ GPU不可用** (红色) - 需要配置

### 详细信息

将鼠标悬停在GPU选项上可查看详细信息：
```
GPU加速状态: 可用
提供者: CUDAExecutionProvider
性能等级: excellent
原因: NVIDIA GPU + CUDA + CUDAExecutionProvider 完整支持
```

## 📊 性能对比

| 硬件配置 | 分辨率 | 图像处理 | 视频处理 | 相对速度 |
|----------|--------|----------|----------|----------|
| RTX 4090 | 1080p | ~1s | ~30fps | 30x |
| RTX 3060 | 1080p | ~2s | ~15fps | 15x |
| RTX 3060 | 720p | ~1s | ~25fps | 25x |
| Intel i7 CPU | 480p | ~10s | ~3fps | 1x |

## 🔧 故障排除

### 常见问题

#### 1. "未检测到NVIDIA GPU"
**原因**: 驱动未安装或GPU不支持
**解决**: 
- 安装最新NVIDIA驱动
- 确认GPU型号支持CUDA

#### 2. "未安装CUDA"
**原因**: CUDA Toolkit未安装
**解决**: 
- 下载安装CUDA 11.8+
- 确保PATH环境变量正确

#### 3. "ONNX Runtime不支持CUDA"
**原因**: 安装了CPU版本的ONNX Runtime
**解决**: 
```bash
pip uninstall onnxruntime
pip install onnxruntime-gpu
```

#### 4. "GPU内存不足"
**原因**: 显存不够或被其他程序占用
**解决**: 
- 关闭其他GPU程序
- 降低处理分辨率
- 使用CPU模式

### 验证GPU配置

运行以下命令验证配置：
```bash
python -c "
import onnxruntime as ort
providers = ort.get_available_providers()
print('可用提供者:', providers)
if 'CUDAExecutionProvider' in providers:
    print('✅ CUDA GPU支持正常')
elif 'DmlExecutionProvider' in providers:
    print('✅ DirectML GPU支持正常')
else:
    print('❌ 仅CPU支持')
"
```

## 💡 使用建议

### 最佳实践

1. **优先使用NVIDIA CUDA**
   - 性能最佳，兼容性好
   - 支持所有AI模型

2. **Windows用户可选DirectML**
   - 支持多种GPU品牌
   - 安装简单，无需CUDA

3. **合理设置处理参数**
   - 根据GPU显存调整批处理大小
   - 高分辨率视频建议分段处理

### 性能优化

1. **关闭不必要的程序**
   - 释放GPU显存
   - 减少系统负载

2. **调整处理质量**
   - 平衡质量和速度
   - 根据需求选择合适设置

3. **监控GPU使用率**
   - 使用任务管理器查看GPU占用
   - 确保GPU得到充分利用

## 🆘 获取帮助

如果遇到GPU配置问题：

1. **运行诊断脚本**
   ```bash
   python scripts/check_environment.py
   ```

2. **查看详细日志**
   - 启动程序时查看GPU检测日志
   - 注意错误信息和警告

3. **联系技术支持**
   - 提供GPU检测报告
   - 说明具体错误信息

---

**GPU加速让AI换脸更快更流畅！** 🚀
