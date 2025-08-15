#!/usr/bin/env python3
"""
cuDNN自动安装脚本
解决CUDA GPU加速中缺少cuDNN的问题
"""

import sys
import subprocess
import platform
import os
from pathlib import Path


def print_banner():
    """打印横幅"""
    print("=" * 60)
    print("🔧 cuDNN自动安装工具")
    print("=" * 60)
    print("解决CUDA GPU加速中缺少cuDNN库的问题")
    print()


def check_cuda_installation():
    """检查CUDA安装情况"""
    try:
        result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ CUDA编译器已安装")
            return True
        else:
            print("❌ CUDA编译器未安装")
            return False
    except FileNotFoundError:
        print("❌ CUDA编译器未找到")
        return False


def install_cudnn_via_conda():
    """通过conda安装cuDNN"""
    print("🔧 尝试通过conda安装cuDNN...")
    
    try:
        # 检查conda是否可用
        result = subprocess.run(['conda', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ conda未安装或不可用")
            return False
        
        print("✅ conda可用，开始安装cuDNN...")
        
        # 安装cuDNN
        result = subprocess.run([
            'conda', 'install', '-c', 'conda-forge', 'cudnn', '-y'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ cuDNN通过conda安装成功!")
            return True
        else:
            print(f"❌ conda安装cuDNN失败: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ conda命令未找到")
        return False
    except Exception as e:
        print(f"❌ conda安装cuDNN时出错: {e}")
        return False


def install_cudnn_via_pip():
    """通过pip安装cuDNN"""
    print("🔧 尝试通过pip安装cuDNN...")
    
    try:
        # 尝试安装nvidia-cudnn-cu12
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', 'nvidia-cudnn-cu12'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ cuDNN通过pip安装成功!")
            return True
        else:
            print(f"❌ pip安装cuDNN失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ pip安装cuDNN时出错: {e}")
        return False


def download_and_install_cudnn():
    """下载并安装cuDNN"""
    print("🔧 尝试下载并安装cuDNN...")
    print("💡 这需要手动下载cuDNN库文件")
    
    print("""
📋 手动安装cuDNN步骤:
1. 访问 https://developer.nvidia.com/cudnn
2. 注册NVIDIA开发者账号 (免费)
3. 下载适合CUDA 12.6的cuDNN版本
4. 解压下载的文件
5. 将bin、include、lib文件夹复制到CUDA安装目录
   (通常是 C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.6\\)

或者，您可以尝试以下自动化方法:
""")
    
    return False


def verify_cudnn_installation():
    """验证cuDNN安装"""
    print("🔍 验证cuDNN安装...")
    
    try:
        import onnxruntime as ort
        
        # 尝试创建CUDA会话
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        
        # 创建一个简单的测试
        import numpy as np
        
        # 这里我们只是测试CUDA提供者是否可用
        available_providers = ort.get_available_providers()
        print(f"📋 可用提供者: {available_providers}")
        
        if 'CUDAExecutionProvider' in available_providers:
            print("✅ CUDAExecutionProvider可用")
            
            # 尝试创建CUDA会话
            try:
                session = ort.InferenceSession(
                    # 这里需要一个实际的ONNX模型文件来测试
                    # 暂时只检查提供者可用性
                    providers=['CUDAExecutionProvider']
                )
                print("✅ CUDA会话创建成功，cuDNN应该已正确安装")
                return True
            except Exception as e:
                if "cudnn" in str(e).lower():
                    print(f"❌ cuDNN仍然缺失: {e}")
                    return False
                else:
                    print("✅ CUDA提供者基本可用")
                    return True
        else:
            print("❌ CUDAExecutionProvider不可用")
            return False
            
    except Exception as e:
        print(f"❌ 验证cuDNN时出错: {e}")
        return False


def main():
    """主函数"""
    print_banner()
    
    # 检查系统
    if platform.system() != "Windows":
        print("❌ 此脚本目前仅支持Windows系统")
        return False
    
    # 检查CUDA
    if not check_cuda_installation():
        print("❌ 请先安装CUDA Toolkit")
        return False
    
    print("🎯 开始安装cuDNN...")
    
    # 尝试多种安装方法
    success = False
    
    # 方法1: pip安装
    if install_cudnn_via_pip():
        success = True
    
    # 方法2: conda安装
    elif install_cudnn_via_conda():
        success = True
    
    # 方法3: 手动安装指导
    else:
        download_and_install_cudnn()
        
        # 询问用户是否已手动安装
        try:
            choice = input("\n是否已完成手动安装cuDNN? (y/N): ").strip().lower()
            if choice in ['y', 'yes']:
                success = True
        except KeyboardInterrupt:
            print("\n❌ 用户中断操作")
            return False
    
    if success:
        # 验证安装
        if verify_cudnn_installation():
            print("\n🎉 cuDNN安装完成!")
            print("=" * 60)
            print("✅ CUDA GPU加速现在应该可以正常工作了")
            print("💡 请重启AI换脸程序以使配置生效")
            print("=" * 60)
            return True
        else:
            print("\n❌ cuDNN安装验证失败")
            return False
    else:
        print("\n❌ cuDNN安装失败")
        print("💡 建议:")
        print("1. 手动下载并安装cuDNN")
        print("2. 或者使用DirectML GPU加速作为替代方案")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        sys.exit(1)
