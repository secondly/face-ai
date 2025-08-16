#!/usr/bin/env python3
"""
GPU环境测试脚本
用于诊断CUDA虚拟环境中的GPU配置问题
"""

import os
import sys
import subprocess

def check_environment():
    """检查当前环境"""
    print("🔍 环境检查")
    print("=" * 50)
    
    # 检查conda环境
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', '未知')
    print(f"Conda环境: {conda_env}")
    
    # 检查Python版本
    print(f"Python版本: {sys.version}")
    
    # 检查Python路径
    print(f"Python路径: {sys.executable}")
    print()

def check_cuda():
    """检查CUDA"""
    print("🚀 CUDA检查")
    print("=" * 50)
    
    try:
        result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ CUDA可用")
            print(result.stdout)
        else:
            print("❌ CUDA不可用")
            print(result.stderr)
    except Exception as e:
        print(f"❌ CUDA检查失败: {e}")
    print()

def check_onnxruntime():
    """检查ONNX Runtime"""
    print("🧠 ONNX Runtime检查")
    print("=" * 50)
    
    try:
        import onnxruntime as ort
        print(f"✅ ONNX Runtime版本: {ort.__version__}")
        
        providers = ort.get_available_providers()
        print(f"可用提供者: {providers}")
        
        if 'CUDAExecutionProvider' in providers:
            print("✅ CUDA提供者可用")
            
            # 尝试创建CUDA会话
            try:
                session = ort.InferenceSession(
                    None,  # 空模型
                    providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
                )
                print("✅ CUDA会话创建成功")
            except Exception as e:
                print(f"❌ CUDA会话创建失败: {e}")
        else:
            print("❌ CUDA提供者不可用")
            
    except ImportError:
        print("❌ ONNX Runtime未安装")
    except Exception as e:
        print(f"❌ ONNX Runtime检查失败: {e}")
    print()

def check_pytorch():
    """检查PyTorch（可选）"""
    print("🔥 PyTorch检查")
    print("=" * 50)
    
    try:
        import torch
        print(f"✅ PyTorch版本: {torch.__version__}")
        print(f"CUDA可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA设备数量: {torch.cuda.device_count()}")
            print(f"当前CUDA设备: {torch.cuda.current_device()}")
            print(f"设备名称: {torch.cuda.get_device_name()}")
    except ImportError:
        print("⚠️ PyTorch未安装")
    except Exception as e:
        print(f"❌ PyTorch检查失败: {e}")
    print()

def check_gpu_memory():
    """检查GPU内存"""
    print("💾 GPU内存检查")
    print("=" * 50)
    
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ nvidia-smi可用")
            # 只显示关键信息
            lines = result.stdout.split('\n')
            for line in lines:
                if 'MiB' in line or 'GPU' in line or 'Driver Version' in line:
                    print(line.strip())
        else:
            print("❌ nvidia-smi不可用")
    except Exception as e:
        print(f"❌ GPU内存检查失败: {e}")
    print()

def main():
    print("🎯 GPU环境诊断工具")
    print("=" * 80)
    print()
    
    check_environment()
    check_cuda()
    check_onnxruntime()
    check_pytorch()
    check_gpu_memory()
    
    print("🎯 诊断完成")
    print("=" * 80)
    print()
    print("💡 如果发现问题，请检查：")
    print("1. 是否在正确的conda环境中 (face-ai-cuda11)")
    print("2. ONNX Runtime版本是否兼容")
    print("3. CUDA工具包是否正确安装")
    print("4. 显卡驱动是否最新")

if __name__ == "__main__":
    main()
