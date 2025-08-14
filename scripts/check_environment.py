#!/usr/bin/env python3
"""
环境检查脚本

检查Deep-Live-Cam运行所需的环境和依赖。
"""

import sys
import os
import platform
import subprocess
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 9:
        print("✓ Python版本符合要求 (>=3.9)")
        return True
    else:
        print("✗ Python版本过低，需要Python 3.9或更高版本")
        return False

def check_system_info():
    """检查系统信息"""
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"架构: {platform.machine()}")
    print(f"处理器: {platform.processor()}")
    
    # 检查内存
    try:
        if platform.system() == "Windows":
            import psutil
            memory = psutil.virtual_memory()
            print(f"总内存: {memory.total // (1024**3)} GB")
            print(f"可用内存: {memory.available // (1024**3)} GB")
        else:
            # Linux/macOS
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemTotal' in line:
                        total_kb = int(line.split()[1])
                        print(f"总内存: {total_kb // (1024**2)} GB")
                        break
    except:
        print("无法获取内存信息")

def check_gpu():
    """检查GPU信息"""
    print("\n检查GPU...")
    
    try:
        # 检查NVIDIA GPU
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ 检测到NVIDIA GPU")
            # 解析GPU信息
            lines = result.stdout.split('\n')
            for line in lines:
                if 'NVIDIA' in line and 'Driver Version' in line:
                    print(f"  {line.strip()}")
                elif '|' in line and 'MiB' in line and 'C' in line:
                    print(f"  {line.strip()}")
            return True
        else:
            print("⚠ 未检测到NVIDIA GPU或nvidia-smi不可用")
            return False
    except FileNotFoundError:
        print("⚠ nvidia-smi命令不存在")
        return False

def check_cuda():
    """检查CUDA"""
    print("\n检查CUDA...")
    
    try:
        result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'release' in line:
                    print(f"✓ {line.strip()}")
                    return True
        else:
            print("⚠ CUDA编译器不可用")
            return False
    except FileNotFoundError:
        print("⚠ nvcc命令不存在")
        return False

def check_ffmpeg():
    """检查FFmpeg"""
    print("\n检查FFmpeg...")
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            first_line = result.stdout.split('\n')[0]
            print(f"✓ {first_line}")
            return True
        else:
            print("✗ FFmpeg不可用")
            return False
    except FileNotFoundError:
        print("✗ FFmpeg未安装")
        return False

def check_python_packages():
    """检查Python包"""
    print("\n检查Python依赖包...")
    
    required_packages = {
        'onnxruntime': 'onnxruntime-gpu',
        'cv2': 'opencv-python', 
        'numpy': 'numpy',
        'insightface': 'insightface',
        'ffmpeg': 'ffmpeg-python',
        'tqdm': 'tqdm',
        'rich': 'rich',
        'yaml': 'pyyaml'
    }
    
    missing_packages = []
    
    for import_name, package_name in required_packages.items():
        try:
            if import_name == 'onnxruntime':
                # 特殊处理onnxruntime
                try:
                    import onnxruntime
                    providers = onnxruntime.get_available_providers()
                    if 'CUDAExecutionProvider' in providers:
                        print(f"✓ {package_name} (GPU支持)")
                    else:
                        print(f"✓ onnxruntime (仅CPU)")
                except ImportError:
                    print(f"✗ {package_name}")
                    missing_packages.append(package_name)
            else:
                __import__(import_name)
                print(f"✓ {package_name}")
        except ImportError:
            print(f"✗ {package_name}")
            missing_packages.append(package_name)
    
    return missing_packages

def check_models(models_dir):
    """检查模型文件"""
    print(f"\n检查模型文件 ({models_dir})...")
    
    required_models = [
        "inswapper_128.onnx",
        "scrfd_10g_bnkps.onnx", 
        "arcface_r100.onnx"
    ]
    
    models_dir = Path(models_dir)
    missing_models = []
    
    for model_name in required_models:
        model_path = models_dir / model_name
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024**2)
            print(f"✓ {model_name} ({size_mb:.1f} MB)")
        else:
            print(f"✗ {model_name}")
            missing_models.append(model_name)
    
    return missing_models

def main():
    print("Deep-Live-Cam 环境检查")
    print("=" * 50)
    
    # 检查Python版本
    python_ok = check_python_version()
    
    # 检查系统信息
    print("\n" + "=" * 50)
    check_system_info()
    
    # 检查GPU
    print("\n" + "=" * 50)
    gpu_ok = check_gpu()
    
    # 检查CUDA
    print("\n" + "=" * 50)
    cuda_ok = check_cuda()
    
    # 检查FFmpeg
    print("\n" + "=" * 50)
    ffmpeg_ok = check_ffmpeg()
    
    # 检查Python包
    print("\n" + "=" * 50)
    missing_packages = check_python_packages()
    
    # 检查模型文件
    print("\n" + "=" * 50)
    models_dir = Path(__file__).parent.parent / "models"
    missing_models = check_models(models_dir)
    
    # 总结
    print("\n" + "=" * 50)
    print("环境检查总结:")
    
    issues = []
    
    if not python_ok:
        issues.append("Python版本过低")
    
    if not ffmpeg_ok:
        issues.append("FFmpeg未安装")
    
    if missing_packages:
        issues.append(f"缺少Python包: {', '.join(missing_packages)}")
    
    if missing_models:
        issues.append(f"缺少模型文件: {', '.join(missing_models)}")
    
    if not gpu_ok:
        print("⚠ 未检测到GPU，将使用CPU模式 (性能较慢)")
    
    if not cuda_ok and gpu_ok:
        print("⚠ 未检测到CUDA，GPU加速可能不可用")
    
    if issues:
        print("\n需要解决的问题:")
        for issue in issues:
            print(f"  ✗ {issue}")
        
        print("\n建议的解决方案:")
        if not python_ok:
            print("  - 升级到Python 3.9或更高版本")
        
        if not ffmpeg_ok:
            print("  - 安装FFmpeg: https://ffmpeg.org/download.html")
        
        if missing_packages:
            print("  - 安装Python依赖: pip install -r requirements.txt")
        
        if missing_models:
            print("  - 下载模型文件: python scripts/download_models.py")
        
        return False
    else:
        print("✓ 环境检查通过！可以开始使用Deep-Live-Cam")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
