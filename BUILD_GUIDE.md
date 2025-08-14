# 🎭 AI换脸工具 - 打包指南

## 📋 概述
本指南将帮助您将AI换脸工具打包成Windows和macOS的可执行文件，方便分发给最终用户。

## 🛠️ 环境准备

### Windows环境
```bash
# 1. 确保Python 3.8+已安装
python --version

# 2. 安装打包依赖
pip install pyinstaller>=5.0.0

# 3. 安装项目依赖
pip install -r requirements.txt
```

### macOS环境
```bash
# 1. 确保Python 3.8+已安装
python3 --version

# 2. 安装打包依赖
pip3 install pyinstaller>=5.0.0

# 3. 安装项目依赖
pip3 install -r requirements.txt
```

## 🚀 快速打包

### 方法1: 使用快速脚本

**Windows:**
```bash
# 双击运行或在命令行执行
quick_build.bat
```

**macOS/Linux:**
```bash
# 添加执行权限并运行
chmod +x quick_build.sh
./quick_build.sh
```

### 方法2: 手动打包

```bash
# 1. 运行打包脚本
python build.py

# 2. 检查输出
# - dist/ 目录包含可执行文件
# - release_*/ 目录包含完整的发布包
```

## 📁 输出结构

打包完成后，您将得到以下文件结构：

```
dist/
├── AI换脸工具.exe (Windows) 或 AI换脸工具 (macOS)
└── 其他依赖文件

release_1.0.0_windows/ (或 release_1.0.0_darwin/)
├── AI换脸工具.exe
├── requirements.txt
├── download_config.json
├── RELEASE_README.md
└── install.bat (Windows) 或 install.sh (macOS)
```

## 🧪 测试步骤

1. **基本启动测试**
   ```bash
   # 运行可执行文件
   ./dist/AI换脸工具
   ```

2. **功能测试**
   - 测试GUI界面启动
   - 测试首次运行的模型下载
   - 测试基本的图片换脸功能
   - 测试视频换脸功能

3. **兼容性测试**
   - 在不同版本的操作系统上测试
   - 在没有Python环境的机器上测试

## 📦 高级配置

### 自定义图标
1. 将图标文件放在 `assets/` 目录
2. 修改 `build_config.py` 中的图标路径
3. 重新打包

### 优化文件大小
1. 安装UPX压缩工具
2. 在 `build_config.py` 中启用UPX压缩
3. 排除不必要的模块

### 添加数字签名 (Windows)
```bash
# 使用signtool为exe文件添加数字签名
signtool sign /f certificate.pfx /p password AI换脸工具.exe
```

## ⚠️ 常见问题

### 1. 打包失败
- 检查所有依赖是否已安装
- 确保Python版本兼容 (3.8+)
- 查看错误日志定位问题

### 2. 可执行文件过大
- 启用UPX压缩
- 排除不必要的模块
- 使用 `--onedir` 模式而非 `--onefile`

### 3. 运行时缺少模块
- 在 `build_config.py` 中添加到 `hidden_imports`
- 检查数据文件是否正确包含

### 4. macOS安全警告
- 用户需要在"系统偏好设置 > 安全性与隐私"中允许运行
- 考虑申请Apple开发者证书进行代码签名

## 📋 发布清单

打包完成后，发布前请确认：

- [ ] 可执行文件能正常启动
- [ ] 首次运行能成功下载模型
- [ ] 基本功能测试通过
- [ ] 包含完整的说明文档
- [ ] 文件大小合理（建议<100MB）
- [ ] 在目标平台上测试通过

## 🔧 自定义打包

如需自定义打包配置，请修改 `build_config.py` 文件：

```python
# 修改应用信息
APP_NAME = "您的应用名称"
APP_VERSION = "1.0.0"

# 修改打包选项
BUILD_CONFIG = {
    "one_file": True,  # 单文件模式
    "console": False,  # 隐藏控制台
    "upx": True,      # 启用压缩
    # ... 其他配置
}
```

## 📞 技术支持

如果在打包过程中遇到问题，请：
1. 查看本文档的常见问题部分
2. 检查PyInstaller官方文档
3. 提交Issue到项目仓库
