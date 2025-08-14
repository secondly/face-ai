#!/usr/bin/env python3
"""
GPU加速支持安装脚本
自动检测GPU类型并安装对应的ONNX Runtime版本
"""

import subprocess
import sys
import platform
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_command(cmd, check=True):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_nvidia_gpu():
    """检查NVIDIA GPU"""
    logger.info("检查NVIDIA GPU...")
    
    # 检查nvidia-smi命令
    success, stdout, stderr = run_command("nvidia-smi", check=False)
    if success:
        logger.info("✅ 检测到NVIDIA GPU")
        return True
    else:
        logger.info("❌ 未检测到NVIDIA GPU或驱动")
        return False

def check_cuda():
    """检查CUDA安装"""
    logger.info("检查CUDA安装...")
    
    success, stdout, stderr = run_command("nvcc --version", check=False)
    if success:
        logger.info("✅ 检测到CUDA")
        return True
    else:
        logger.info("❌ 未检测到CUDA")
        return False

def check_current_onnxruntime():
    """检查当前ONNX Runtime版本"""
    logger.info("检查当前ONNX Runtime...")
    
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        logger.info(f"当前ONNX Runtime提供者: {providers}")
        
        if 'CUDAExecutionProvider' in providers:
            logger.info("✅ 已安装GPU版本的ONNX Runtime")
            return 'gpu'
        elif 'DmlExecutionProvider' in providers:
            logger.info("✅ 已安装DirectML版本的ONNX Runtime")
            return 'directml'
        else:
            logger.info("⚠️ 当前为CPU版本的ONNX Runtime")
            return 'cpu'
    except ImportError:
        logger.info("❌ 未安装ONNX Runtime")
        return 'none'

def install_onnxruntime_gpu():
    """安装GPU版本的ONNX Runtime"""
    logger.info("安装GPU版本的ONNX Runtime...")
    
    # 卸载现有版本
    logger.info("卸载现有ONNX Runtime...")
    run_command("pip uninstall onnxruntime onnxruntime-gpu onnxruntime-directml -y", check=False)
    
    # 安装GPU版本
    logger.info("安装onnxruntime-gpu...")
    success, stdout, stderr = run_command("pip install onnxruntime-gpu")
    
    if success:
        logger.info("✅ GPU版本安装成功")
        return True
    else:
        logger.error(f"❌ GPU版本安装失败: {stderr}")
        return False

def install_onnxruntime_directml():
    """安装DirectML版本的ONNX Runtime"""
    logger.info("安装DirectML版本的ONNX Runtime...")
    
    # 卸载现有版本
    logger.info("卸载现有ONNX Runtime...")
    run_command("pip uninstall onnxruntime onnxruntime-gpu onnxruntime-directml -y", check=False)
    
    # 安装DirectML版本
    logger.info("安装onnxruntime-directml...")
    success, stdout, stderr = run_command("pip install onnxruntime-directml")
    
    if success:
        logger.info("✅ DirectML版本安装成功")
        return True
    else:
        logger.error(f"❌ DirectML版本安装失败: {stderr}")
        return False

def install_onnxruntime_cpu():
    """安装CPU版本的ONNX Runtime"""
    logger.info("安装CPU版本的ONNX Runtime...")
    
    # 卸载现有版本
    run_command("pip uninstall onnxruntime onnxruntime-gpu onnxruntime-directml -y", check=False)
    
    # 安装CPU版本
    success, stdout, stderr = run_command("pip install onnxruntime")
    
    if success:
        logger.info("✅ CPU版本安装成功")
        return True
    else:
        logger.error(f"❌ CPU版本安装失败: {stderr}")
        return False

def main():
    """主函数"""
    print("🚀 GPU加速支持安装脚本")
    print("=" * 50)

    # 使用新的GPU检测器
    try:
        sys.path.append(str(Path(__file__).parent.parent))
        from utils.gpu_detector import GPUDetector

        detector = GPUDetector()
        gpu_result = detector.detect_all()

        # 打印详细检测报告
        detector.print_detailed_report(gpu_result)

        # 根据检测结果提供安装建议
        recommended_config = gpu_result.get('recommended_config', {})
        config_type = recommended_config.get('type', 'cpu_only')

        print("\n" + "=" * 50)
        print("🎯 安装建议")
        print("=" * 50)

        if config_type == 'cuda_gpu':
            print("✅ 检测到完整的NVIDIA GPU + CUDA环境")
            print("推荐: 已经配置完成，无需额外安装")

        elif config_type == 'directml_gpu':
            print("✅ 检测到DirectML GPU支持")
            print("推荐: 已经配置完成，无需额外安装")

        else:
            print("❌ GPU加速不可用")
            print(f"原因: {recommended_config.get('reason', '未知')}")
            print("\n🔧 解决方案:")

            # 检查具体问题并提供解决方案
            nvidia = gpu_result.get('nvidia_gpu', {})
            cuda = gpu_result.get('cuda', {})
            onnx = gpu_result.get('onnx_providers', {})

            if not nvidia.get('available'):
                print("1. 安装NVIDIA GPU驱动:")
                print("   - 访问 https://www.nvidia.com/drivers/")
                print("   - 下载并安装最新驱动")

            if not cuda.get('available'):
                print("2. 安装CUDA Toolkit:")
                print("   - 访问 https://developer.nvidia.com/cuda-downloads")
                print("   - 下载并安装CUDA 11.8或更高版本")

            if not onnx.get('available') or 'CUDAExecutionProvider' not in onnx.get('providers', []):
                print("3. 安装GPU版本的ONNX Runtime:")
                current_version = check_current_onnxruntime()
                if current_version != 'gpu':
                    choice = input("   是否现在安装GPU版本的ONNX Runtime? (y/n): ").lower()
                    if choice == 'y':
                        if install_onnxruntime_gpu():
                            print("   ✅ GPU版本安装完成!")
                        else:
                            print("   ❌ GPU版本安装失败")
                            # 尝试DirectML作为备选
                            if platform.system() == "Windows":
                                print("   🔄 尝试安装DirectML版本...")
                                if install_onnxruntime_directml():
                                    print("   ✅ DirectML版本安装完成!")
                                else:
                                    print("   ❌ DirectML版本也安装失败")
                    else:
                        print("   跳过GPU版本安装")
                else:
                    print("   ✅ 已安装GPU版本")

    except ImportError:
        print("❌ GPU检测器不可用，使用传统检测方法")
        # 回退到原有逻辑
        _legacy_main()

    print("\n" + "=" * 50)
    print("安装完成! 请重新启动AI换脸应用程序")

def _legacy_main():
    """传统检测方法"""
    # 检查操作系统
    os_name = platform.system()
    logger.info(f"操作系统: {os_name}")

    # 检查当前ONNX Runtime状态
    current_version = check_current_onnxruntime()

    # 检查GPU支持
    has_nvidia = check_nvidia_gpu()
    has_cuda = check_cuda()

    # 决定安装策略
    if has_nvidia and has_cuda:
        logger.info("🎯 推荐安装: CUDA GPU版本")
        if current_version != 'gpu':
            choice = input("是否安装GPU版本的ONNX Runtime? (y/n): ").lower()
            if choice == 'y':
                if install_onnxruntime_gpu():
                    print("\n✅ GPU加速安装完成!")
                else:
                    print("\n❌ GPU加速安装失败")
            else:
                print("跳过GPU版本安装")
        else:
            print("✅ 已安装GPU版本，无需重复安装")

    elif os_name == "Windows":
        logger.info("🎯 推荐安装: DirectML版本 (支持AMD/Intel GPU)")
        if current_version != 'directml':
            choice = input("是否安装DirectML版本的ONNX Runtime? (y/n): ").lower()
            if choice == 'y':
                if install_onnxruntime_directml():
                    print("\n✅ DirectML加速安装完成!")
                else:
                    print("\n❌ DirectML加速安装失败")
            else:
                print("跳过DirectML版本安装")
        else:
            print("✅ 已安装DirectML版本，无需重复安装")

    else:
        logger.info("🎯 推荐安装: CPU版本")
        if current_version == 'none':
            if install_onnxruntime_cpu():
                print("\n✅ CPU版本安装完成!")
            else:
                print("\n❌ CPU版本安装失败")
        else:
            print("✅ 已安装ONNX Runtime")

if __name__ == "__main__":
    main()
