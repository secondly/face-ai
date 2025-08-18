# 🎭 AI换脸【秘灵】

基于ONNX的高性能AI换脸工具，支持图片和视频处理，现已集成背景替换功能！

## ✨ 主要功能

- 🎯 **智能换脸**: 基于InsightFace的高质量人脸替换
- 🎨 **背景替换**: 支持多种背景替换技术（新功能！）
- 🎬 **视频处理**: 支持MP4、AVI、MOV等格式
- 👥 **多人脸处理**: 智能识别和选择性替换
- 🚀 **GPU加速**: 支持CUDA和DirectML加速
- 🖥️ **现代化GUI**: 直观易用的图形界面

## 🎨 背景替换功能 (新增)

### 支持的模式
- **BackgroundMattingV2** (推荐) - 高质量背景替换
- **MODNet** (快速) - 实时人像分割
- **U2Net** (通用) - 通用目标分割
- **Rembg** (简单) - 简单易用的背景移除

### 背景选择
- 📷 **单张背景**: 选择一张背景图片
- 📁 **随机背景**: 从文件夹中随机选择背景

### 使用方法
1. 勾选"启用背景替换"
2. 选择替换模式
3. 选择背景图片或文件夹
4. 开始换脸处理

详细说明请查看: [背景替换功能文档](docs/BACKGROUND_REPLACEMENT.md)

## 🚀 快速开始

### 环境要求
- Python 3.9-3.11
- Windows 10/11 (推荐)
- NVIDIA GPU (可选，用于加速)

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd ai-face-swap
```

2. **创建虚拟环境**
```bash
conda create -n face-ai-cuda11 python=3.10
conda activate face-ai-cuda11
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **安装背景替换依赖** (可选)
```bash
python scripts/install_background_deps.py
```

5. **下载模型**
```bash
python scripts/download_models.py
```

6. **启动程序**
```bash
python main_pyqt.py
```

## 📖 使用说明

### 基础换脸
1. 点击"🤖 初始化AI"加载模型
2. 选择源人脸图像
3. 选择目标图像或视频
4. 设置输出路径
5. 点击"🚀 开始换脸"

### 背景替换
1. 完成基础换脸设置
2. 勾选"启用背景替换"
3. 选择背景替换模式
4. 选择背景图片或文件夹
5. 开始处理

### 多人脸处理
1. 勾选"🎯 多人脸选择"
2. 选择目标文件后会弹出人脸选择界面
3. 选择要替换的人脸
4. 开始处理

## 🛠️ 高级功能

- **GPU内存管理**: 智能内存使用和自动回退
- **性能优化**: 多线程处理和缓存机制
- **实时预览**: 处理过程中的实时预览
- **批量处理**: 支持批量文件处理

## 📁 项目结构

```
ai-face-swap/
├── core/                   # 核心功能模块
│   ├── face_swapper.py    # 换脸引擎
│   └── background_replacer.py  # 背景替换引擎 (新增)
├── gui/                   # 图形界面
│   └── pyqt_gui.py       # 主界面
├── models/               # AI模型文件
├── scripts/              # 工具脚本
│   └── install_background_deps.py  # 背景替换依赖安装 (新增)
├── docs/                 # 文档
│   └── BACKGROUND_REPLACEMENT.md  # 背景替换文档 (新增)
└── test_background_replacement.py  # 背景替换测试 (新增)
```

## 🔧 故障排除

### 常见问题
- **GPU不可用**: 使用一键GPU配置功能
- **模型加载失败**: 检查模型文件是否完整
- **背景替换失败**: 确保已安装相关依赖

### 获取帮助
- 查看详细文档: `docs/` 目录
- 运行测试脚本: `python test_background_replacement.py`
- 检查系统环境: `python test_gpu.py`

## 📄 许可证

本项目仅供学习和研究使用，请遵守相关法律法规。

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

**⚠️ 免责声明**: 本工具仅供学习研究使用，请勿用于非法用途。使用者需对使用后果承担责任。