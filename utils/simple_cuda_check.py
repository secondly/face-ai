#!/usr/bin/env python3
"""
简化的CUDA检查工具
避免复杂操作导致界面卡死
"""

import subprocess
import sys
from typing import Dict

def quick_cuda_check() -> Dict:
    """快速CUDA检查"""
    result = {
        'onnxruntime_info': check_onnxruntime(),
        'cuda_available': check_cuda_command(),
        'gpu_available': check_nvidia_smi(),
        'main_issue': None,
        'simple_solution': None,
        'status': 'unknown'
    }
    
    # 分析主要问题
    result['main_issue'], result['simple_solution'] = analyze_main_issue(result)
    
    # 确定状态
    if result['main_issue'] is None:
        result['status'] = 'good'
    elif 'onnxruntime' in result['main_issue'].lower():
        result['status'] = 'fixable'
    else:
        result['status'] = 'warning'
    
    return result

def check_onnxruntime() -> Dict:
    """检查ONNX Runtime"""
    try:
        import onnxruntime as ort
        version = ort.__version__
        providers = ort.get_available_providers()
        
        # 检查安装的包
        try:
            import pkg_resources
            installed_packages = [pkg.project_name.lower() for pkg in pkg_resources.working_set]
            has_gpu_package = 'onnxruntime-gpu' in installed_packages
            has_cpu_package = 'onnxruntime' in installed_packages
        except:
            has_gpu_package = False
            has_cpu_package = True
        
        return {
            'installed': True,
            'version': version,
            'providers': providers,
            'has_cuda_provider': 'CUDAExecutionProvider' in providers,
            'has_gpu_package': has_gpu_package,
            'has_cpu_package': has_cpu_package
        }
    except ImportError:
        return {
            'installed': False
        }

def check_cuda_command() -> bool:
    """检查CUDA命令"""
    try:
        result = subprocess.run(['nvcc', '--version'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def check_nvidia_smi() -> bool:
    """检查nvidia-smi"""
    try:
        result = subprocess.run(['nvidia-smi'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def analyze_main_issue(result: Dict) -> tuple:
    """分析主要问题"""
    onnx_info = result['onnxruntime_info']
    
    if not onnx_info.get('installed'):
        return "ONNX Runtime未安装", "安装ONNX Runtime GPU版本"
    
    if not result['gpu_available']:
        return "未检测到NVIDIA GPU或驱动问题", "检查GPU驱动程序安装"
    
    if not result['cuda_available']:
        return "CUDA未安装", "安装CUDA Toolkit"
    
    if not onnx_info.get('has_cuda_provider'):
        return "ONNX Runtime不支持CUDA", "安装onnxruntime-gpu版本"
    
    if onnx_info.get('has_cpu_package') and not onnx_info.get('has_gpu_package'):
        return "安装了CPU版本的ONNX Runtime", "卸载onnxruntime，安装onnxruntime-gpu"
    
    if onnx_info.get('has_cpu_package') and onnx_info.get('has_gpu_package'):
        return "同时安装了CPU和GPU版本", "卸载所有版本，重新安装onnxruntime-gpu"
    
    # 版本兼容性检查
    version = onnx_info.get('version', '')
    if version.startswith('1.19') or version.startswith('1.18'):
        return "ONNX Runtime版本可能不兼容CUDA 12.3", "安装兼容版本：onnxruntime-gpu==1.16.3"
    
    return None, None

def test_gpu_simple() -> Dict:
    """简单的GPU测试"""
    try:
        import onnxruntime as ort
        
        # 只检查提供者，不创建会话
        providers = ort.get_available_providers()
        
        if 'CUDAExecutionProvider' in providers:
            return {
                'test_result': 'cuda_available',
                'message': 'CUDA提供者可用'
            }
        elif 'DmlExecutionProvider' in providers:
            return {
                'test_result': 'directml_available', 
                'message': 'DirectML提供者可用'
            }
        else:
            return {
                'test_result': 'cpu_only',
                'message': '仅CPU提供者可用'
            }
    except ImportError:
        return {
            'test_result': 'no_onnxruntime',
            'message': 'ONNX Runtime未安装'
        }
    except Exception as e:
        return {
            'test_result': 'error',
            'message': f'测试失败: {str(e)}'
        }

def format_simple_report(result: Dict) -> str:
    """格式化简单报告"""
    report = "🔍 快速GPU配置检查\n"
    report += "=" * 40 + "\n\n"
    
    # ONNX Runtime状态
    onnx_info = result['onnxruntime_info']
    if onnx_info.get('installed'):
        report += f"📦 ONNX Runtime: ✅ 已安装 (v{onnx_info.get('version', 'Unknown')})\n"
        report += f"   GPU包: {'✅' if onnx_info.get('has_gpu_package') else '❌'}\n"
        report += f"   CUDA支持: {'✅' if onnx_info.get('has_cuda_provider') else '❌'}\n"
    else:
        report += "📦 ONNX Runtime: ❌ 未安装\n"
    
    # GPU状态
    report += f"\n🎮 NVIDIA GPU: {'✅' if result['gpu_available'] else '❌'}\n"
    report += f"🚀 CUDA: {'✅' if result['cuda_available'] else '❌'}\n"
    
    # 主要问题
    if result['main_issue']:
        report += f"\n❌ 主要问题: {result['main_issue']}\n"
        report += f"💡 建议解决方案: {result['simple_solution']}\n"
    else:
        report += f"\n✅ 配置看起来正常\n"
    
    # GPU测试
    gpu_test = test_gpu_simple()
    report += f"\n🧪 GPU测试: {gpu_test['message']}\n"
    
    return report

def main():
    """主函数"""
    result = quick_cuda_check()
    report = format_simple_report(result)
    print(report)
    return result

if __name__ == "__main__":
    main()
