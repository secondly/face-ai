"""
FFmpeg安装检查和配置工具
"""

import subprocess
import platform
import os
from pathlib import Path


def check_ffmpeg_installation():
    """检查FFmpeg安装状态"""
    print("🔍 检查FFmpeg安装状态...")
    
    # 检查系统类型
    system = platform.system()
    print(f"操作系统: {system}")
    
    # 尝试查找FFmpeg
    ffmpeg_path = find_ffmpeg()
    ffprobe_path = find_ffprobe()
    
    if ffmpeg_path and ffprobe_path:
        print(f"✅ FFmpeg已找到: {ffmpeg_path}")
        print(f"✅ FFprobe已找到: {ffprobe_path}")
        
        # 获取版本信息
        try:
            result = subprocess.run([ffmpeg_path, '-version'], 
                                  capture_output=True, text=True, check=True)
            version_line = result.stdout.split('\n')[0]
            print(f"📋 版本信息: {version_line}")
            
            # 检查编码器支持
            result = subprocess.run([ffmpeg_path, '-encoders'], 
                                  capture_output=True, text=True, check=True)
            if 'libx264' in result.stdout:
                print("✅ H.264编码器支持: 是")
            else:
                print("❌ H.264编码器支持: 否")
                
            if 'aac' in result.stdout:
                print("✅ AAC音频编码器支持: 是")
            else:
                print("❌ AAC音频编码器支持: 否")
                
        except Exception as e:
            print(f"❌ 获取版本信息失败: {e}")
            
        return True
    else:
        print("❌ FFmpeg未找到")
        print_installation_guide()
        return False


def find_ffmpeg():
    """查找FFmpeg可执行文件"""
    possible_paths = get_possible_ffmpeg_paths()
    
    # 首先尝试PATH中的ffmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return 'ffmpeg'
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # 尝试其他路径
    for path in possible_paths:
        try:
            if os.path.exists(path):
                subprocess.run([path, '-version'], capture_output=True, check=True)
                return path
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            continue
    
    return None


def find_ffprobe():
    """查找FFprobe可执行文件"""
    possible_paths = get_possible_ffprobe_paths()
    
    # 首先尝试PATH中的ffprobe
    try:
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
        return 'ffprobe'
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # 尝试其他路径
    for path in possible_paths:
        try:
            if os.path.exists(path):
                subprocess.run([path, '-version'], capture_output=True, check=True)
                return path
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            continue
    
    return None


def get_possible_ffmpeg_paths():
    """获取可能的FFmpeg路径"""
    if platform.system() == "Windows":
        return [
            "ffmpeg.exe",
            "ffmpeg/ffmpeg.exe",
            "ffmpeg/bin/ffmpeg.exe",
            "C:/ffmpeg/bin/ffmpeg.exe",
            "C:/Program Files/ffmpeg/bin/ffmpeg.exe",
            os.path.expanduser("~/ffmpeg/bin/ffmpeg.exe")
        ]
    else:
        return [
            "ffmpeg",
            "./ffmpeg",
            "/usr/local/bin/ffmpeg",
            "/usr/bin/ffmpeg",
            "/opt/homebrew/bin/ffmpeg",  # Mac M1
            os.path.expanduser("~/bin/ffmpeg")
        ]


def get_possible_ffprobe_paths():
    """获取可能的FFprobe路径"""
    if platform.system() == "Windows":
        return [
            "ffprobe.exe",
            "ffmpeg/ffprobe.exe", 
            "ffmpeg/bin/ffprobe.exe",
            "C:/ffmpeg/bin/ffprobe.exe",
            "C:/Program Files/ffmpeg/bin/ffprobe.exe",
            os.path.expanduser("~/ffmpeg/bin/ffprobe.exe")
        ]
    else:
        return [
            "ffprobe",
            "./ffprobe",
            "/usr/local/bin/ffprobe",
            "/usr/bin/ffprobe", 
            "/opt/homebrew/bin/ffprobe",  # Mac M1
            os.path.expanduser("~/bin/ffprobe")
        ]


def print_installation_guide():
    """打印安装指南"""
    system = platform.system()
    
    print("\n📖 FFmpeg安装指南:")
    print("=" * 50)
    
    if system == "Windows":
        print("🪟 Windows安装方法:")
        print("1. 下载FFmpeg: https://ffmpeg.org/download.html#build-windows")
        print("2. 解压到 C:/ffmpeg/")
        print("3. 将 C:/ffmpeg/bin 添加到系统PATH")
        print("4. 或者将ffmpeg.exe和ffprobe.exe复制到项目目录")
        
    elif system == "Darwin":  # macOS
        print("🍎 macOS安装方法:")
        print("1. 使用Homebrew: brew install ffmpeg")
        print("2. 使用MacPorts: sudo port install ffmpeg")
        print("3. 手动下载: https://ffmpeg.org/download.html#build-mac")
        
    elif system == "Linux":
        print("🐧 Linux安装方法:")
        print("1. Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg")
        print("2. CentOS/RHEL: sudo yum install ffmpeg")
        print("3. Arch Linux: sudo pacman -S ffmpeg")
        print("4. 手动编译: https://ffmpeg.org/download.html#build-linux")
    
    print("\n💡 验证安装:")
    print("在命令行运行: ffmpeg -version")
    print("应该显示FFmpeg版本信息")


if __name__ == "__main__":
    check_ffmpeg_installation()
