"""
下载FFmpeg便携版到项目目录
"""

import requests
import zipfile
import os
from pathlib import Path
import platform


def download_ffmpeg():
    """下载FFmpeg便携版"""
    print("🚀 开始下载FFmpeg便携版...")
    
    # 创建ffmpeg目录
    ffmpeg_dir = Path("ffmpeg")
    ffmpeg_dir.mkdir(exist_ok=True)
    
    # Windows版本的FFmpeg下载链接
    if platform.system() == "Windows":
        # 使用GitHub上的预编译版本
        url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        zip_filename = "ffmpeg-win64.zip"
        
        print(f"📥 下载地址: {url}")
        print("⏳ 正在下载，请稍候...")
        
        try:
            # 下载文件
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(zip_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r📊 下载进度: {percent:.1f}%", end="", flush=True)
            
            print(f"\n✅ 下载完成: {zip_filename}")
            
            # 解压文件
            print("📦 正在解压...")
            with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
                zip_ref.extractall("temp_ffmpeg")
            
            # 移动文件到正确位置
            temp_dir = Path("temp_ffmpeg")
            extracted_dirs = list(temp_dir.iterdir())
            
            if extracted_dirs:
                source_bin = extracted_dirs[0] / "bin"
                if source_bin.exists():
                    # 复制可执行文件
                    for exe_file in source_bin.glob("*.exe"):
                        target_file = ffmpeg_dir / exe_file.name
                        exe_file.replace(target_file)
                        print(f"📋 复制: {exe_file.name}")
            
            # 清理临时文件
            print("🧹 清理临时文件...")
            os.remove(zip_filename)
            
            # 删除临时目录
            import shutil
            shutil.rmtree("temp_ffmpeg")
            
            print("✅ FFmpeg安装完成!")
            print(f"📁 安装位置: {ffmpeg_dir.absolute()}")
            
            # 验证安装
            verify_installation()
            
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            print("💡 请尝试手动下载:")
            print("1. 访问: https://ffmpeg.org/download.html")
            print("2. 下载Windows版本")
            print("3. 解压到项目的ffmpeg文件夹")
            
    else:
        print("❌ 此脚本仅支持Windows系统")
        print("💡 Linux/Mac用户请使用包管理器安装:")
        print("Ubuntu/Debian: sudo apt install ffmpeg")
        print("macOS: brew install ffmpeg")


def verify_installation():
    """验证FFmpeg安装"""
    print("\n🔍 验证安装...")
    
    ffmpeg_exe = Path("ffmpeg/ffmpeg.exe")
    ffprobe_exe = Path("ffmpeg/ffprobe.exe")
    
    if ffmpeg_exe.exists() and ffprobe_exe.exists():
        print("✅ FFmpeg文件存在")
        
        # 测试运行
        try:
            import subprocess
            result = subprocess.run([str(ffmpeg_exe), "-version"], 
                                  capture_output=True, text=True, check=True)
            version_line = result.stdout.split('\n')[0]
            print(f"✅ 版本验证成功: {version_line}")
            
            print("\n🎉 FFmpeg便携版安装成功!")
            print("现在您的AI换脸程序可以保留视频音频了!")
            
        except Exception as e:
            print(f"❌ 版本验证失败: {e}")
    else:
        print("❌ FFmpeg文件未找到")


if __name__ == "__main__":
    download_ffmpeg()
