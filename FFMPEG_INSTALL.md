# FFmpeg 便携版安装指南

## 🚀 快速安装

### 方法1：自动下载（推荐）

运行下载脚本：
```bash
python download_ffmpeg.py
```

这将自动：
- 📥 下载最新的FFmpeg Windows版本
- 📦 解压到项目的 `ffmpeg/` 目录
- ✅ 验证安装是否成功

### 方法2：手动下载

1. **下载FFmpeg**
   - 访问：https://github.com/BtbN/FFmpeg-Builds/releases
   - 下载：`ffmpeg-master-latest-win64-gpl.zip`

2. **解压安装**
   ```
   项目根目录/
   ├── ffmpeg/
   │   ├── ffmpeg.exe
   │   ├── ffprobe.exe
   │   └── ffplay.exe
   ├── core/
   ├── gui/
   └── ...
   ```

3. **验证安装**
   ```bash
   python utils/ffmpeg_checker.py
   ```

## 🔍 验证安装

运行检查工具：
```bash
python utils/ffmpeg_checker.py
```

应该看到：
```
✅ FFmpeg已找到: ffmpeg/ffmpeg.exe
✅ FFprobe已找到: ffmpeg/ffprobe.exe
📋 版本信息: ffmpeg version ...
✅ H.264编码器支持: 是
✅ AAC音频编码器支持: 是
```

## 🎵 音频保留功能

安装FFmpeg后，AI换脸程序将自动：
- 🔍 检测原视频的音轨
- 🎬 处理换脸视频（无音频）
- 🎵 从原视频提取音频
- 🔗 将音频合并到换脸视频
- ✅ 输出带音频的最终视频

## ❓ 常见问题

### Q: 为什么选择便携版？
A: 
- ✅ 无需管理员权限
- ✅ 不影响系统PATH
- ✅ 项目自包含
- ✅ 易于分发和部署

### Q: 如何更新FFmpeg？
A: 重新运行 `python download_ffmpeg.py` 即可

### Q: 支持其他操作系统吗？
A: 
- Windows: ✅ 支持便携版安装
- Linux: 使用 `sudo apt install ffmpeg`
- macOS: 使用 `brew install ffmpeg`

## 🛠️ 故障排除

### 如果下载失败：
1. 检查网络连接
2. 尝试使用VPN
3. 手动下载并解压

### 如果音频仍然丢失：
1. 运行 `python utils/ffmpeg_checker.py`
2. 检查日志中的FFmpeg相关信息
3. 确保原视频确实包含音轨

## 📁 文件结构

安装完成后的目录结构：
```
AI换脸项目/
├── ffmpeg/                 # FFmpeg便携版
│   ├── ffmpeg.exe          # 主程序
│   ├── ffprobe.exe         # 媒体信息分析
│   └── ffplay.exe          # 播放器（可选）
├── core/
│   └── face_swapper.py     # 自动检测ffmpeg/目录
├── utils/
│   └── ffmpeg_checker.py   # 安装验证工具
└── download_ffmpeg.py      # 自动下载脚本
```
