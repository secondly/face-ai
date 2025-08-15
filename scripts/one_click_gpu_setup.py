#!/usr/bin/env python3
"""
一键GPU配置脚本 - 傻瓜式GPU配置
自动检测硬件环境并安装最适合的GPU加速组件
"""

import sys
import subprocess
import platform
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def print_banner():
    """打印横幅"""
    print("=" * 60)
    print("🚀 AI换脸工具 - 一键GPU配置")
    print("=" * 60)
    print("自动检测您的硬件环境并配置最佳的GPU加速方案")
    print()


def detect_gpu_environment():
    """检测GPU环境"""
    try:
        # 添加项目根目录到路径
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        from utils.gpu_detector import GPUDetector
        
        print("🔍 正在检测GPU环境...")
        detector = GPUDetector()
        result = detector.detect_all()
        
        # 打印简化的检测报告
        print(f"\n💻 系统: {result['system']}")
        
        nvidia = result['nvidia_gpu']
        if nvidia.get('available'):
            print(f"🎮 NVIDIA GPU: ✅ 检测到 {nvidia['count']} 个GPU")
            for gpu in nvidia['gpus']:
                print(f"   📊 {gpu['name']} ({gpu['memory_mb']}MB)")
        else:
            print(f"🎮 NVIDIA GPU: ❌ 未检测到")
        
        cuda = result['cuda']
        if cuda.get('available'):
            print(f"🚀 CUDA: ✅ 已安装 ({cuda['version_info']})")
        else:
            print(f"🚀 CUDA: ❌ 未安装")
        
        onnx = result['onnx_providers']
        if onnx.get('available'):
            providers = onnx['providers']
            print(f"🧠 ONNX Runtime: ✅ 已安装 (版本 {onnx['onnxruntime_version']})")
            if 'CUDAExecutionProvider' in providers:
                print(f"   🚀 CUDA支持: ✅")
            elif 'DmlExecutionProvider' in providers:
                print(f"   ⚡ DirectML支持: ✅")
            else:
                print(f"   💻 仅CPU支持")
        else:
            print(f"🧠 ONNX Runtime: ❌ 未安装")
        
        return result
        
    except ImportError as e:
        print(f"❌ GPU检测模块导入失败: {e}")
        return None
    except Exception as e:
        print(f"❌ GPU环境检测失败: {e}")
        return None


def get_recommended_action(gpu_result):
    """获取推荐的配置方案"""
    if not gpu_result:
        return "install_cpu", "安装CPU版本ONNX Runtime"

    recommended = gpu_result.get('recommended_config', {})
    config_type = recommended.get('type', 'cpu_only')

    # 检查NVIDIA GPU和CUDA可用性
    nvidia = gpu_result.get('nvidia_gpu', {}).get('available', False)
    cuda = gpu_result.get('cuda', {}).get('available', False)
    system = gpu_result.get('system', '')

    # 优先推荐NVIDIA CUDA（即使当前使用DirectML）
    if nvidia and cuda:
        # 检查当前是否已经是CUDA配置
        onnx = gpu_result.get('onnx_providers', {})
        if (onnx.get('available') and 'CUDAExecutionProvider' in onnx.get('providers', [])):
            return "already_configured", "NVIDIA CUDA GPU加速已正确配置"
        else:
            return "install_cuda", "升级到NVIDIA CUDA GPU支持 (性能更佳)"

    elif config_type == 'directml_gpu':
        return "already_configured", "DirectML GPU加速已配置 (如需更好性能，建议安装NVIDIA驱动和CUDA)"
    elif config_type == 'cuda_gpu':
        return "already_configured", "NVIDIA CUDA GPU加速已正确配置"
    else:
        # 需要配置GPU支持
        if system == "Windows":
            return "install_directml", "安装DirectML GPU支持 (通用)"
        else:
            return "install_cpu", "安装CPU版本 (兼容性最佳)"


def install_onnxruntime_package(package_name, description):
    """安装ONNX Runtime包"""
    print(f"\n📦 {description}...")
    
    try:
        # 先卸载现有版本
        print("🗑️ 卸载现有ONNX Runtime版本...")
        subprocess.run([
            sys.executable, '-m', 'pip', 'uninstall', 
            'onnxruntime', 'onnxruntime-gpu', 'onnxruntime-directml', '-y'
        ], check=False, capture_output=True)
        
        # 安装新版本
        print(f"⬇️ 安装 {package_name}...")
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', package_name
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {package_name} 安装成功!")
            return True
        else:
            print(f"❌ 安装失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 安装过程中出现错误: {e}")
        return False


def verify_installation():
    """验证安装结果"""
    print("\n🔍 验证安装结果...")
    
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        
        print(f"📋 可用提供者: {', '.join(providers)}")
        
        if 'CUDAExecutionProvider' in providers:
            print("🚀 NVIDIA CUDA GPU加速: ✅ 可用")
            return "cuda"
        elif 'DmlExecutionProvider' in providers:
            print("⚡ DirectML GPU加速: ✅ 可用")
            return "directml"
        elif 'CPUExecutionProvider' in providers:
            print("💻 CPU模式: ✅ 可用")
            return "cpu"
        else:
            print("❌ 未检测到任何可用的执行提供者")
            return "none"
            
    except ImportError:
        print("❌ ONNX Runtime导入失败")
        return "none"
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return "none"


def main():
    """主函数"""
    print_banner()
    
    # 检测GPU环境
    gpu_result = detect_gpu_environment()
    
    # 获取推荐方案
    action, description = get_recommended_action(gpu_result)
    
    print(f"\n🎯 推荐方案: {description}")
    
    if action == "already_configured":
        print("✅ 您的GPU加速已正确配置，无需额外操作!")
        return True
    
    # 确认是否继续
    print(f"\n是否要执行推荐的配置方案？")
    print(f"方案: {description}")
    
    try:
        choice = input("\n请输入 y/Y 继续，其他键取消: ").strip().lower()
        if choice not in ['y', 'yes']:
            print("❌ 用户取消操作")
            return False
    except KeyboardInterrupt:
        print("\n❌ 用户中断操作")
        return False
    
    # 执行安装
    success = False
    
    if action == "install_cuda":
        success = install_onnxruntime_package("onnxruntime-gpu", "安装NVIDIA CUDA GPU支持")
    elif action == "install_directml":
        success = install_onnxruntime_package("onnxruntime-directml", "安装DirectML GPU支持")
    elif action == "install_cpu":
        success = install_onnxruntime_package("onnxruntime", "安装CPU版本ONNX Runtime")
    
    if success:
        # 验证安装
        result_type = verify_installation()
        
        if result_type != "none":
            print("\n🎉 GPU配置完成!")
            print("=" * 60)
            print("✅ 配置成功! 您现在可以使用GPU加速功能了")
            print("💡 请重启AI换脸程序以使配置生效")
            print("=" * 60)
            return True
        else:
            print("\n❌ 配置验证失败，请检查安装过程中的错误信息")
            return False
    else:
        print("\n❌ 配置失败，请查看上述错误信息")
        return False


def silent_install(config_type="auto"):
    """静默安装模式 (供GUI调用)"""
    try:
        # 检测环境
        gpu_result = detect_gpu_environment()
        
        if config_type == "auto":
            action, _ = get_recommended_action(gpu_result)
        else:
            action = f"install_{config_type}"
        
        # 执行安装
        if action == "install_cuda":
            return install_onnxruntime_package("onnxruntime-gpu", "安装NVIDIA CUDA GPU支持")
        elif action == "install_directml":
            return install_onnxruntime_package("onnxruntime-directml", "安装DirectML GPU支持")
        elif action == "install_cpu":
            return install_onnxruntime_package("onnxruntime", "安装CPU版本ONNX Runtime")
        else:
            return True  # 已配置
            
    except Exception as e:
        print(f"❌ 静默安装失败: {e}")
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
