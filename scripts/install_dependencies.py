#!/usr/bin/env python3
"""
依赖安装脚本

自动检测环境并安装所需的Python依赖包。
"""

import sys
import subprocess
import platform
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 9:
        print("✅ Python版本符合要求 (>=3.9)")
        return True
    else:
        print("❌ Python版本过低，需要Python 3.9或更高版本")
        return False

def check_pip():
    """检查pip是否可用"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ pip可用")
            return True
        else:
            print("❌ pip不可用")
            return False
    except Exception:
        print("❌ pip检查失败")
        return False

def upgrade_pip():
    """升级pip"""
    print("正在升级pip...")
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ pip升级成功")
            return True
        else:
            print(f"⚠ pip升级失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ pip升级异常: {e}")
        return False

def detect_gpu():
    """检测GPU类型"""
    try:
        # 检查NVIDIA GPU
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 检测到NVIDIA GPU")
            return "nvidia"
    except FileNotFoundError:
        pass
    
    # 检查AMD GPU (Linux)
    if platform.system() == "Linux":
        try:
            result = subprocess.run(['rocm-smi'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ 检测到AMD GPU")
                return "amd"
        except FileNotFoundError:
            pass
    
    # 检查Intel GPU (Windows)
    if platform.system() == "Windows":
        try:
            result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                  capture_output=True, text=True)
            if "Intel" in result.stdout:
                print("✅ 检测到Intel GPU")
                return "intel"
        except Exception:
            pass
    
    print("⚠ 未检测到GPU或GPU不支持，将使用CPU模式")
    return "cpu"

def get_requirements_content(gpu_type="cpu"):
    """获取requirements内容"""
    base_requirements = [
        "numpy>=1.21.0",
        "opencv-python>=4.8.0",
        "insightface>=0.7.3",
        "ffmpeg-python>=0.2.0",
        "tqdm>=4.64.0",
        "rich>=13.0.0",
        "pyyaml>=6.0",
    ]
    
    # 根据GPU类型选择ONNX Runtime
    if gpu_type == "nvidia":
        base_requirements.append("onnxruntime-gpu>=1.15.0")
    elif gpu_type == "amd":
        # AMD GPU支持 (ROCm)
        base_requirements.append("onnxruntime-rocm>=1.15.0")
    elif gpu_type == "intel":
        # Intel GPU支持
        base_requirements.append("onnxruntime-openvino>=1.15.0")
    else:
        # CPU版本
        base_requirements.append("onnxruntime>=1.15.0")
    
    return base_requirements

def install_requirements(requirements_list):
    """安装依赖包"""
    print(f"正在安装 {len(requirements_list)} 个依赖包...")
    
    failed_packages = []
    
    for i, package in enumerate(requirements_list, 1):
        print(f"[{i}/{len(requirements_list)}] 安装 {package}")
        
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', package
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  ✅ {package} 安装成功")
            else:
                print(f"  ❌ {package} 安装失败: {result.stderr}")
                failed_packages.append(package)
                
        except Exception as e:
            print(f"  ❌ {package} 安装异常: {e}")
            failed_packages.append(package)
    
    return failed_packages

def install_optional_packages():
    """安装可选包"""
    optional_packages = [
        "gfpgan>=1.3.8",
        "basicsr>=1.4.2", 
        "facexlib>=0.3.0",
        "psutil>=5.9.0"
    ]
    
    print("\n安装可选增强包...")
    print("这些包用于图像增强功能，安装失败不影响基础功能")
    
    for package in optional_packages:
        print(f"尝试安装 {package}")
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', package
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"  ✅ {package} 安装成功")
            else:
                print(f"  ⚠ {package} 安装失败 (可选包)")
                
        except subprocess.TimeoutExpired:
            print(f"  ⚠ {package} 安装超时 (可选包)")
        except Exception:
            print(f"  ⚠ {package} 安装异常 (可选包)")

def create_requirements_file(gpu_type="cpu"):
    """创建requirements.txt文件"""
    requirements_content = get_requirements_content(gpu_type)
    
    requirements_file = PROJECT_ROOT / "requirements.txt"
    
    # 备份现有文件
    if requirements_file.exists():
        backup_file = PROJECT_ROOT / "requirements.txt.backup"
        requirements_file.rename(backup_file)
        print(f"已备份现有requirements.txt为 {backup_file}")
    
    # 写入新的requirements.txt
    with open(requirements_file, 'w', encoding='utf-8') as f:
        f.write("# Deep-Live-Cam 依赖包清单\n")
        f.write(f"# 自动生成 - GPU类型: {gpu_type}\n\n")
        
        for package in requirements_content:
            f.write(f"{package}\n")
    
    print(f"✅ 已生成 requirements.txt (GPU类型: {gpu_type})")
    return requirements_file

def verify_installation():
    """验证安装"""
    print("\n验证关键包安装...")
    
    critical_packages = [
        ("numpy", "import numpy"),
        ("cv2", "import cv2"),
        ("onnxruntime", "import onnxruntime"),
        ("insightface", "import insightface"),
    ]
    
    failed_imports = []
    
    for package_name, import_statement in critical_packages:
        try:
            exec(import_statement)
            print(f"✅ {package_name} 导入成功")
        except ImportError as e:
            print(f"❌ {package_name} 导入失败: {e}")
            failed_imports.append(package_name)
    
    if failed_imports:
        print(f"\n❌ 以下关键包导入失败: {', '.join(failed_imports)}")
        return False
    else:
        print("\n✅ 所有关键包验证通过")
        return True

def main():
    """主函数"""
    print("Deep-Live-Cam 依赖安装脚本")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        print("请升级Python版本后重试")
        return 1
    
    # 检查pip
    if not check_pip():
        print("请安装pip后重试")
        return 1
    
    # 升级pip
    upgrade_pip()
    
    # 检测GPU
    gpu_type = detect_gpu()
    
    # 创建requirements.txt
    requirements_file = create_requirements_file(gpu_type)
    
    # 获取依赖列表
    requirements_list = get_requirements_content(gpu_type)
    
    # 安装依赖
    print(f"\n开始安装依赖包 (GPU类型: {gpu_type})")
    failed_packages = install_requirements(requirements_list)
    
    # 安装可选包
    install_optional_packages()
    
    # 验证安装
    if verify_installation():
        print("\n🎉 依赖安装完成！")
        
        if failed_packages:
            print(f"\n⚠ 以下包安装失败: {', '.join(failed_packages)}")
            print("可以稍后手动安装这些包")
        
        print("\n下一步:")
        print("1. 运行环境检查: python scripts/check_environment.py")
        print("2. 下载模型: python scripts/quick_setup.py")
        print("3. 或使用GUI: python scripts/model_downloader_gui.py")
        
        return 0
    else:
        print("\n❌ 依赖安装验证失败")
        print("请检查错误信息并手动安装失败的包")
        return 1

if __name__ == "__main__":
    sys.exit(main())
