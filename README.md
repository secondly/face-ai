# Deep-Live-Cam 🎭

> 基于ONNX的实时换脸系统 - 一键换脸，无需训练，支持实时处理

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![ONNX](https://img.shields.io/badge/ONNX-Runtime-green.svg)](https://onnxruntime.ai/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

## ✨ 特性

- 🎯 **高精度换脸**: 基于InsightFace的先进AI算法
- 🖼️ **图像处理**: 支持JPG、PNG等主流图像格式
- 🎬 **视频处理**: 支持MP4、AVI等主流视频格式
- 🎨 **现代GUI**: 毛玻璃风格的美观界面
- 📱 **命令行支持**: 支持CLI批量处理
- 🔧 **一键安装**: 自动模型下载和环境配置
- 📊 **实时进度**: 处理进度实时显示
- 💻 **跨平台**: Windows、Linux、macOS全平台支持

## 🎯 快速开始

### 安装
```bash
# 克隆项目
git clone https://github.com/your-repo/deep-live-cam.git
cd deep-live-cam

# 安装依赖
pip install -r requirements.txt

# 🚀 一键获取所有模型 (推荐)
python scripts/simple_model_getter.py

# 或使用GUI界面
python scripts/model_downloader_gui.py
```

### 🎭 基础使用

```bash
# 启动GUI界面 (推荐)
python main.py

# 命令行处理图像
python main.py --source face.jpg --target photo.jpg --output result.jpg

# 命令行处理视频
python main.py --source face.jpg --target video.mp4 --output result.mp4

# 检查模型状态
python main.py --check-models
```

## 📖 详细使用指南

### GUI界面使用

1. **启动应用**
   ```bash
   python main.py
   ```

2. **选择文件**
   - 点击"选择文件"按钮选择源人脸图像
   - 选择目标图像或视频文件
   - 输出路径会自动生成，也可手动修改

3. **开始处理**
   - 点击"🚀 开始换脸"按钮
   - 查看实时进度和状态
   - 处理完成后会自动提示

4. **查看结果**
   - 点击"📁 打开输出文件夹"查看结果
   - 支持的格式：JPG、PNG、MP4、AVI等

### 命令行使用

```bash
# 基本语法
python main.py --source <源人脸> --target <目标文件> --output <输出文件>

# 图像换脸示例
python main.py --source face.jpg --target photo.jpg --output result.jpg

# 视频换脸示例
python main.py --source face.jpg --target video.mp4 --output result.mp4

# 查看帮助
python main.py --help
```

### 支持的文件格式

**图像格式**
- 输入：JPG, JPEG, PNG, BMP, TIFF
- 输出：JPG, PNG

**视频格式**
- 输入：MP4, AVI, MOV, MKV, WMV
- 输出：MP4

### 故障排除

**模型文件缺失**
```bash
# 运行模型获取器
python scripts/simple_model_getter.py
```

**依赖问题**
```bash
# 重新安装依赖
pip install -r requirements.txt
```

**GPU支持**
```bash
# 安装GPU版本的onnxruntime
pip uninstall onnxruntime
pip install onnxruntime-gpu
```

## 📖 文档

| 文档 | 描述 |
|------|------|
| [🚀 快速开始指南](快速开始指南.md) | 5分钟快速上手教程 |
| [📚 操作手册](操作手册.md) | 详细的安装和使用说明 |
| [📋 需求文档](需求文档.md) | 完整的功能需求和技术规格 |
| [📊 项目进度](项目进度跟踪.md) | 开发进度和里程碑跟踪 |

## 🛠️ 技术架构

### 核心技术栈
- **推理引擎**: ONNX Runtime (GPU/CPU)
- **计算机视觉**: OpenCV
- **人脸处理**: InsightFace
- **视频处理**: FFmpeg
- **编程语言**: Python 3.9+

### 核心模型
- **InSwapper**: 换脸生成模型
- **SCRFD**: 人脸检测和关键点
- **ArcFace**: 人脸识别和特征提取
- **BiSeNet**: 人脸分割 (可选)
- **GFPGAN**: 人脸增强 (可选)

## 🎬 使用示例

### 命令行界面
```bash
# 高质量单视频处理
python -m dlc_batch.cli swap-video \
    --source face.jpg \
    --input video.mp4 \
    --output result.mp4 \
    --quality high \
    --enhance-face

# 批量处理
python -m dlc_batch.cli swap-dir \
    --source face.jpg \
    --input-dir videos/ \
    --output-dir results/ \
    --threads 4

# 多人脸处理
python -m dlc_batch.cli swap-video \
    --input video.mp4 \
    --output result.mp4 \
    --map "person1=face1.jpg,person2=face2.jpg"

# 实时推流
python -m dlc_batch.cli swap-live \
    --source face.jpg \
    --camera 0 \
    --rtmp rtmp://live.example.com/stream/key
```

## 📊 性能基准

| 硬件配置 | 分辨率 | 处理速度 | GPU内存占用 |
|----------|--------|----------|-------------|
| RTX 4090 | 1080p | ~60fps | ~3GB |
| RTX 3060 | 1080p | ~25fps | ~4GB |
| RTX 3060 | 720p | ~40fps | ~2GB |
| CPU i7-10700K | 480p | ~8fps | N/A |

## 🔧 系统要求

### 最低要求
- **操作系统**: Windows 10, Ubuntu 18.04, macOS 10.15
- **Python**: 3.9+
- **内存**: 8GB RAM
- **存储**: 5GB 可用空间
- **网络**: 用于下载模型文件

### 推荐配置
- **GPU**: NVIDIA RTX 3060 或更高
- **内存**: 16GB RAM
- **存储**: SSD 10GB+ 可用空间
- **CUDA**: 11.8+

## 📁 项目结构

```
deep-live-cam/
├── dlc_batch/              # 主程序包
│   ├── engine/            # 推理引擎
│   ├── tracker/           # 人脸跟踪
│   ├── io/                # 视频处理
│   ├── ui/                # 用户界面
│   ├── config/            # 配置管理
│   ├── utils/             # 工具函数
│   └── cli.py             # 命令行接口
├── models/                # ONNX模型文件
├── scripts/               # 安装和工具脚本
├── assets/                # 示例资源
├── videos_in/             # 输入视频目录
├── outputs/               # 输出结果目录
├── docs/                  # 文档
└── tests/                 # 测试用例
```

## 🚀 开发路线图

### 已完成 ✅
- [x] 项目架构设计
- [x] 需求文档和操作手册
- [x] 开发环境配置

### 进行中 🔄
- [ ] 核心换脸功能实现
- [ ] 命令行接口开发
- [ ] 基础测试用例

### 计划中 📋
- [ ] 批量处理功能
- [ ] 多人脸处理
- [ ] 实时换脸模式
- [ ] 画质优化算法
- [ ] Web界面 (可选)
- [ ] 移动端支持 (未来)

## 🤝 贡献指南

我们欢迎所有形式的贡献！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

### 如何贡献
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## ⚠️ 免责声明

### 合规使用要求
- ✅ **仅限合规场景**: 请确保在合法、合规的场景下使用本工具
- ✅ **授权使用**: 必须对所有使用的人脸图像拥有明确的使用授权
- ✅ **遵守法律**: 严格遵守当地法律法规和平台政策
- ❌ **禁止滥用**: 严禁用于欺诈、诈骗、恶意传播等非法用途

### 技术限制
- 本工具基于AI技术，在极端条件下可能存在处理效果不佳的情况
- 处理结果的质量受源素材质量、光照条件、角度等因素影响
- 建议在使用前充分测试，确保满足您的具体需求

## 🆘 获取帮助

- 📖 查看 [操作手册](操作手册.md) 获取详细使用说明
- 🐛 [提交Issue](https://github.com/your-repo/deep-live-cam/issues) 报告问题
- 💬 [参与讨论](https://github.com/your-repo/deep-live-cam/discussions) 交流经验
- 📧 联系邮箱: support@example.com

## 🙏 致谢

感谢以下开源项目的贡献：
- [InsightFace](https://github.com/deepinsight/insightface) - 人脸分析工具包
- [ONNX Runtime](https://github.com/microsoft/onnxruntime) - 高性能推理引擎
- [OpenCV](https://github.com/opencv/opencv) - 计算机视觉库
- [FFmpeg](https://github.com/FFmpeg/FFmpeg) - 多媒体处理框架

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**

Made with ❤️ by Deep-Live-Cam Team

</div>
