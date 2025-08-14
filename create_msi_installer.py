#!/usr/bin/env python3
"""
创建MSI安装程序
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_previous_builds():
    """清理之前的构建文件"""
    print("🧹 清理之前的构建文件...")
    
    # 清理目录
    dirs_to_clean = ["build", "dist", "installer_temp"]
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"✅ 清理 {dir_name}")
    
    # 清理文件
    files_to_clean = [
        "*.spec",
        "*.msi",
        "*.exe"
    ]
    
    for pattern in files_to_clean:
        for file_path in Path(".").glob(pattern):
            if file_path.name not in ["main_pyqt.py", "ffmpeg.exe"]:  # 保留主程序和ffmpeg
                file_path.unlink()
                print(f"✅ 清理 {file_path}")

def create_installer_structure():
    """创建安装程序结构"""
    print("📁 创建安装程序结构...")
    
    installer_dir = Path("installer_temp")
    installer_dir.mkdir(exist_ok=True)
    
    # 复制核心文件
    core_files = [
        "main_pyqt.py",
        "auto_downloader.py",
        "download_config.json",
        "requirements.txt"
    ]
    
    for file_name in core_files:
        if Path(file_name).exists():
            shutil.copy2(file_name, installer_dir)
            print(f"✅ 复制 {file_name}")
    
    # 复制目录
    core_dirs = ["gui", "core", "scripts"]
    for dir_name in core_dirs:
        if Path(dir_name).exists():
            shutil.copytree(dir_name, installer_dir / dir_name)
            print(f"✅ 复制 {dir_name}")
    
    # 复制ffmpeg（如果存在）
    if Path("ffmpeg").exists():
        shutil.copytree("ffmpeg", installer_dir / "ffmpeg")
        print("✅ 复制 ffmpeg")
    
    return installer_dir

def create_installer_scripts(installer_dir):
    """创建安装脚本"""
    print("📝 创建安装脚本...")
    
    # 创建改进的安装脚本
    install_script = '''@echo off
chcp 65001 >nul
title AI换脸工具 v1.0.0 安装程序
echo 🎭 AI换脸工具 v1.0.0 安装程序
echo ================================
echo.

REM 检查Python
echo [1/6] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python
    echo.
    echo 请先安装Python 3.8或更高版本
    echo 下载地址：https://www.python.org/downloads/
    echo.
    echo 安装Python时请勾选"Add Python to PATH"选项
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% 检测通过
echo.

REM 创建程序目录
echo [2/6] 准备安装目录...
set INSTALL_DIR=%USERPROFILE%\\AI换脸工具
echo 📁 安装目录: %INSTALL_DIR%

if exist "%INSTALL_DIR%" (
    echo ⚠️  检测到已存在的安装，正在更新...
    rmdir /s /q "%INSTALL_DIR%" 2>nul
    timeout /t 1 >nul
)

mkdir "%INSTALL_DIR%" 2>nul
echo ✅ 安装目录准备完成
echo.

REM 复制文件
echo [3/6] 复制程序文件...
echo 正在复制文件，请稍候...
xcopy /E /I /Q "%~dp0*" "%INSTALL_DIR%\\" >nul
if errorlevel 1 (
    echo ❌ 文件复制失败
    pause
    exit /b 1
)
echo ✅ 程序文件复制完成
echo.

REM 检查并安装Python依赖
echo [4/6] 检查Python依赖包...
cd /d "%INSTALL_DIR%"

REM 检查每个依赖包
set PACKAGES_TO_INSTALL=
echo 正在检查已安装的包...

python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo   - PyQt5: 需要安装
    set PACKAGES_TO_INSTALL=%PACKAGES_TO_INSTALL% PyQt5
) else (
    echo   - PyQt5: ✅ 已安装
)

python -c "import cv2" >nul 2>&1
if errorlevel 1 (
    echo   - opencv-python: 需要安装
    set PACKAGES_TO_INSTALL=%PACKAGES_TO_INSTALL% opencv-python
) else (
    echo   - opencv-python: ✅ 已安装
)

python -c "import numpy" >nul 2>&1
if errorlevel 1 (
    echo   - numpy: 需要安装
    set PACKAGES_TO_INSTALL=%PACKAGES_TO_INSTALL% numpy
) else (
    echo   - numpy: ✅ 已安装
)

python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo   - Pillow: 需要安装
    set PACKAGES_TO_INSTALL=%PACKAGES_TO_INSTALL% Pillow
) else (
    echo   - Pillow: ✅ 已安装
)

python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo   - requests: 需要安装
    set PACKAGES_TO_INSTALL=%PACKAGES_TO_INSTALL% requests
) else (
    echo   - requests: ✅ 已安装
)

python -c "import tqdm" >nul 2>&1
if errorlevel 1 (
    echo   - tqdm: 需要安装
    set PACKAGES_TO_INSTALL=%PACKAGES_TO_INSTALL% tqdm
) else (
    echo   - tqdm: ✅ 已安装
)

python -c "import onnxruntime" >nul 2>&1
if errorlevel 1 (
    echo   - onnxruntime: 需要安装
    set PACKAGES_TO_INSTALL=%PACKAGES_TO_INSTALL% onnxruntime
) else (
    echo   - onnxruntime: ✅ 已安装
)

python -c "import insightface" >nul 2>&1
if errorlevel 1 (
    echo   - insightface: 需要安装
    set PACKAGES_TO_INSTALL=%PACKAGES_TO_INSTALL% insightface
) else (
    echo   - insightface: ✅ 已安装
)

python -c "import skimage" >nul 2>&1
if errorlevel 1 (
    echo   - scikit-image: 需要安装
    set PACKAGES_TO_INSTALL=%PACKAGES_TO_INSTALL% scikit-image
) else (
    echo   - scikit-image: ✅ 已安装
)

echo.

if "%PACKAGES_TO_INSTALL%"=="" (
    echo ✅ 所有依赖包已安装，跳过安装步骤
) else (
    echo 📦 需要安装以下包:%PACKAGES_TO_INSTALL%
    echo 正在安装，这可能需要几分钟...
    echo.

    for %%p in (%PACKAGES_TO_INSTALL%) do (
        echo 正在安装 %%p...
        pip install %%p --progress-bar on
        if errorlevel 1 (
            echo ❌ %%p 安装失败
            echo 请检查网络连接并重试
            pause
            exit /b 1
        )
        echo ✅ %%p 安装完成
        echo.
    )
)

echo [5/6] 创建桌面快捷方式...
set SHORTCUT_PATH=%USERPROFILE%\\Desktop\\AI换脸工具.lnk
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%INSTALL_DIR%\\启动AI换脸工具.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = '%INSTALL_DIR%\\启动AI换脸工具.bat'; $Shortcut.Save()" >nul 2>&1
echo ✅ 桌面快捷方式创建完成
echo.

echo [6/6] 完成安装...
echo.
echo 🎉 安装完成！
echo ================================
echo 📁 安装位置: %INSTALL_DIR%
echo 🖥️  桌面快捷方式: AI换脸工具.lnk
echo.
echo 💡 使用提示:
echo   - 双击桌面快捷方式启动程序
echo   - 首次运行会自动下载AI模型(约800MB)
echo   - 请确保网络连接稳定
echo.
echo 按任意键退出安装程序...
pause >nul
'''
    
    install_path = installer_dir / "安装.bat"
    with open(install_path, "w", encoding="utf-8") as f:
        f.write(install_script)
    
    # 创建启动脚本
    launcher_script = '''@echo off
chcp 65001 >nul
echo 🎭 AI换脸工具 v1.0.0
echo ==================
echo.

cd /d "%~dp0"

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python环境异常
    echo 请重新运行安装程序
    pause
    exit /b 1
)

echo 正在启动AI换脸工具...
echo.

REM 启动程序
python main_pyqt.py

REM 如果程序异常退出
if errorlevel 1 (
    echo.
    echo ❌ 程序异常退出
    echo 请检查错误信息或重新安装
    echo.
    pause
)
'''
    
    launcher_path = installer_dir / "启动AI换脸工具.bat"
    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write(launcher_script)
    
    # 创建卸载脚本
    uninstall_script = '''@echo off
chcp 65001 >nul
echo 🗑️  AI换脸工具卸载程序
echo ========================
echo.

set INSTALL_DIR=%USERPROFILE%\\AI换脸工具
set SHORTCUT_PATH=%USERPROFILE%\\Desktop\\AI换脸工具.lnk

echo 确定要卸载AI换脸工具吗？
echo.
echo 这将删除以下内容：
echo - 程序文件: %INSTALL_DIR%
echo - 桌面快捷方式: %SHORTCUT_PATH%
echo.
echo 注意：下载的模型文件和输出结果将被保留
echo.
pause

echo 正在卸载...
echo.

REM 删除程序目录
if exist "%INSTALL_DIR%" (
    rmdir /s /q "%INSTALL_DIR%"
    echo ✅ 程序文件已删除
) else (
    echo ⚠️  程序目录不存在
)

REM 删除桌面快捷方式
if exist "%SHORTCUT_PATH%" (
    del "%SHORTCUT_PATH%"
    echo ✅ 桌面快捷方式已删除
) else (
    echo ⚠️  桌面快捷方式不存在
)

echo.
echo 🎉 卸载完成！
echo.
pause
'''
    
    uninstall_path = installer_dir / "卸载.bat"
    with open(uninstall_path, "w", encoding="utf-8") as f:
        f.write(uninstall_script)
    
    # 创建说明文件
    readme_content = """# AI换脸工具 v1.0.0 安装包

## 安装步骤

### 1. 确保Python环境
- 需要Python 3.8或更高版本
- 下载地址：https://www.python.org/downloads/
- 安装时请勾选"Add Python to PATH"

### 2. 运行安装程序
双击 "安装.bat" 开始安装
- 程序会自动安装到用户目录下的"AI换脸工具"文件夹
- 自动安装所需的Python依赖包
- 在桌面创建快捷方式

### 3. 启动程序
- 双击桌面的"AI换脸工具"快捷方式
- 或者进入安装目录，运行"启动AI换脸工具.bat"

## 系统要求
- Windows 10/11 (64位)
- Python 3.8或更高版本
- 4GB+ RAM
- 2GB+ 可用磁盘空间
- 稳定的网络连接（用于下载模型）

## 卸载
运行安装目录中的"卸载.bat"

## 注意事项
- 首次运行会自动下载AI模型（约800MB）
- 请确保网络连接稳定
- 请合法使用，尊重他人隐私

## 问题反馈
https://github.com/secondly/face-ai/issues
"""
    
    readme_path = installer_dir / "安装说明.txt"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("✅ 安装脚本创建完成")

def create_zip_package():
    """创建ZIP安装包"""
    print("📦 创建ZIP安装包...")
    
    installer_dir = Path("installer_temp")
    if not installer_dir.exists():
        print("❌ 安装目录不存在")
        return False
    
    # 创建ZIP文件
    zip_name = "AI换脸工具_v1.0.0_安装包.zip"
    
    try:
        shutil.make_archive(
            zip_name.replace('.zip', ''),
            'zip',
            installer_dir
        )
        print(f"✅ ZIP安装包创建完成: {zip_name}")
        return True
    except Exception as e:
        print(f"❌ ZIP创建失败: {e}")
        return False

def main():
    """主函数"""
    print("🎭 AI换脸工具 - MSI安装程序制作工具")
    print("=" * 50)
    print("📦 创建简洁的安装包")
    print()
    
    # 清理之前的构建
    clean_previous_builds()
    
    # 创建安装程序结构
    installer_dir = create_installer_structure()
    
    # 创建安装脚本
    create_installer_scripts(installer_dir)
    
    # 创建ZIP包
    if create_zip_package():
        print("\n🎉 安装包制作完成！")
        print("📁 临时目录: installer_temp/")
        print("📦 安装包: AI换脸工具_v1.0.0_安装包.zip")
        print("\n📋 用户使用步骤:")
        print("1. 解压ZIP文件")
        print("2. 双击'安装.bat'进行安装")
        print("3. 使用桌面快捷方式启动程序")
        
        print("\n💡 安装包特点:")
        print("- ✅ 自动检查Python环境")
        print("- ✅ 自动安装依赖包")
        print("- ✅ 创建桌面快捷方式")
        print("- ✅ 提供卸载功能")
        print("- ✅ 包含详细说明文档")
        
        # 清理临时目录
        print("\n🧹 清理临时文件...")
        shutil.rmtree(installer_dir)
        print("✅ 清理完成")
        
        return True
    else:
        print("\n❌ 安装包制作失败")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
