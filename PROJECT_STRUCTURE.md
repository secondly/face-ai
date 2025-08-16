# AI换脸工具 - 项目结构说明

## 📁 核心文件结构

```
face-ai/
├── 🚀 启动文件
│   ├── main_pyqt.py              # 主程序入口
│   ├── start_ai_face_swap.py     # Python启动器
│   └── start_ai_face_swap.bat    # Windows启动器
│
├── 🔧 环境配置
│   ├── setup_venv.py             # 虚拟环境设置器
│   ├── requirements.txt          # Python依赖列表
│   └── venv/                     # 虚拟环境目录
│
├── 🤖 核心功能
│   ├── core/
│   │   └── face_swapper.py       # 人脸交换核心逻辑
│   ├── gui/
│   │   ├── pyqt_gui.py          # 主界面
│   │   ├── startup_checker.py   # 启动检测界面
│   │   ├── download_manager.py  # 下载管理器
│   │   └── video_frame_face_selector.py # 视频帧选择器
│   └── utils/
│       ├── system_checker.py    # 系统检测器
│       ├── gpu_detector.py      # GPU检测器
│       ├── simple_cuda_check.py # 简化CUDA检查
│       └── ffmpeg_checker.py    # FFmpeg检查器
│
├── 📦 资源文件
│   ├── models/                  # AI模型文件
│   │   ├── inswapper_128.onnx   # 人脸交换模型
│   │   ├── scrfd_10g_bnkps.onnx # 人脸检测模型
│   │   └── arcface_r100.onnx    # 人脸识别模型
│   ├── ffmpeg/                  # FFmpeg工具
│   │   ├── ffmpeg.exe
│   │   ├── ffplay.exe
│   │   └── ffprobe.exe
│   └── config/                  # 配置文件
│
├── 🛠️ 工具脚本
│   ├── scripts/
│   │   ├── copy_models.py       # 模型复制工具
│   │   ├── download_buffalo_l.py # buffalo_l模型下载器
│   │   ├── download_models.py   # 模型下载器
│   │   ├── fix_gpu_simple.py    # GPU问题修复器
│   │   └── quick_fix_onnx.py    # ONNX Runtime快速修复
│   ├── auto_downloader.py       # 自动下载器
│   ├── download_ffmpeg.py       # FFmpeg下载器
│   └── download_config.json     # 下载配置
│
├── 📤 输出目录
│   ├── output/                  # 处理结果输出
│   ├── face_swap_results/       # 换脸结果
│   └── temp/                    # 临时文件
│
└── 📚 文档
    └── README.md                # 项目说明
```

## 🚀 使用方法

### 1. 首次设置
```bash
# 创建虚拟环境并安装依赖
python setup_venv.py
```

### 2. 启动程序
```bash
# 方法1: 双击启动器
start_ai_face_swap.bat

# 方法2: Python启动器
python start_ai_face_swap.py

# 方法3: 直接启动
venv/Scripts/python.exe main_pyqt.py
```

### 3. 问题修复
```bash
# 修复GPU问题
python scripts/fix_gpu_simple.py

# 修复ONNX Runtime
python scripts/quick_fix_onnx.py

# 下载模型文件
python scripts/download_buffalo_l.py
python scripts/copy_models.py
```

## 🔧 核心组件说明

### 启动检测系统
- `gui/startup_checker.py` - 启动前自动检测配置
- `utils/system_checker.py` - 系统状态检测器
- `utils/gpu_detector.py` - GPU环境检测

### 模型管理系统
- `scripts/download_buffalo_l.py` - 下载InsightFace模型包
- `scripts/copy_models.py` - 复制模型到项目目录
- `auto_downloader.py` - 自动下载管理器

### GPU支持系统
- `scripts/fix_gpu_simple.py` - GPU问题一键修复
- `utils/simple_cuda_check.py` - 快速CUDA检查
- `scripts/quick_fix_onnx.py` - ONNX Runtime版本修复

### 虚拟环境系统
- `setup_venv.py` - 创建独立Python环境
- `start_ai_face_swap.py` - 虚拟环境启动器
- `venv/` - 隔离的依赖环境

## 💡 设计特点

1. **模块化设计** - 每个功能独立，便于维护
2. **用户友好** - 一键操作，无需技术知识
3. **环境隔离** - 虚拟环境避免依赖冲突
4. **自动检测** - 启动前自动检测并修复问题
5. **智能降级** - GPU不可用时自动使用CPU模式

## 🗑️ 已清理的文件

以下文件已被删除，因为它们是重复的、测试的或不再需要的：

- 测试文件: `test_*.py`
- 重复脚本: `scripts/complete_status_check.py` 等
- 临时文档: 各种中文说明文档
- 缓存文件: `__pycache__` 目录
- 实验性功能: GPU内存配置、系统监控等

项目现在更加简洁，只保留核心功能和必要文件。
