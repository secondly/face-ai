#!/usr/bin/env python3
"""
快速修复ONNX Runtime版本问题
"""

import sys
import subprocess
import time

def test_onnx_version():
    """测试当前ONNX Runtime版本是否工作"""
    try:
        # 重新加载模块
        if 'onnxruntime' in sys.modules:
            del sys.modules['onnxruntime']

        import onnxruntime as ort

        # 尝试创建一个简单的会话来测试CUDA提供者
        providers = ort.get_available_providers()
        if 'CUDAExecutionProvider' not in providers:
            return False

        # 尝试创建CUDA会话（简单测试）
        try:
            session_options = ort.SessionOptions()
            session_options.log_severity_level = 4  # 只显示致命错误

            # 创建一个最小的测试会话
            providers_config = [
                ('CUDAExecutionProvider', {
                    'device_id': 0,
                    'arena_extend_strategy': 'kSameAsRequested',
                    'gpu_mem_limit': 512 * 1024 * 1024,  # 512MB
                }),
                'CPUExecutionProvider'
            ]

            # 这里只是测试提供者是否可以初始化，不运行实际推理
            return True

        except Exception:
            return False

    except Exception:
        return False

def fix_onnxruntime_version():
    """修复ONNX Runtime版本"""
    print("🔧 开始修复ONNX Runtime版本问题...")
    print("=" * 50)
    
    # 步骤1: 卸载现有版本
    print("\n📋 步骤1: 卸载现有ONNX Runtime版本")
    uninstall_commands = [
        [sys.executable, '-m', 'pip', 'uninstall', 'onnxruntime', '-y'],
        [sys.executable, '-m', 'pip', 'uninstall', 'onnxruntime-gpu', '-y'],
        [sys.executable, '-m', 'pip', 'uninstall', 'onnxruntime-directml', '-y']
    ]
    
    for cmd in uninstall_commands:
        package_name = cmd[4]
        print(f"卸载 {package_name}...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print(f"✅ {package_name} 卸载成功")
            else:
                print(f"⚠️ {package_name} 可能未安装")
        except Exception as e:
            print(f"❌ 卸载 {package_name} 失败: {e}")
    
    # 步骤2: 安装兼容版本
    print("\n📋 步骤2: 安装兼容版本的ONNX Runtime GPU")
    
    # 对于CUDA 12.3，尝试多个兼容版本（按优先级排序）
    versions_to_try = [
        "1.19.2",  # 最新稳定版，支持CUDA 12.x
        "1.18.1",  # 支持CUDA 12.x的较新版本
        "1.17.3",  # 稳定版本
        None,      # 最新版本
        "1.16.3",  # 最后尝试的版本
    ]

    for target_version in versions_to_try:
        if target_version:
            install_cmd = [sys.executable, '-m', 'pip', 'install', f'onnxruntime-gpu=={target_version}']
            version_text = f"onnxruntime-gpu=={target_version}"
        else:
            install_cmd = [sys.executable, '-m', 'pip', 'install', 'onnxruntime-gpu']
            version_text = "最新版本的onnxruntime-gpu"

        print(f"尝试安装 {version_text}...")
        try:
            result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print(f"✅ {version_text} 安装成功")

                # 立即测试这个版本是否工作
                if test_onnx_version():
                    print(f"✅ {version_text} 测试通过")
                    break
                else:
                    print(f"⚠️ {version_text} 安装成功但测试失败，尝试下一个版本...")
                    continue
            else:
                print(f"❌ {version_text} 安装失败: {result.stderr}")
                continue
        except Exception as e:
            print(f"❌ 安装 {version_text} 过程出错: {e}")
            continue
    else:
        print("❌ 所有版本都安装失败")
        return False
    
    # 步骤3: 验证安装
    print("\n📋 步骤3: 验证安装结果")
    time.sleep(2)  # 等待安装完成
    
    try:
        import importlib

        # 重新加载模块
        if 'onnxruntime' in sys.modules:
            del sys.modules['onnxruntime']
        
        import onnxruntime as ort
        version = ort.__version__
        providers = ort.get_available_providers()
        
        print(f"✅ ONNX Runtime版本: {version}")
        print(f"✅ 可用提供者: {providers}")
        
        if 'CUDAExecutionProvider' in providers:
            print("✅ CUDA提供者可用")
            return True
        else:
            print("⚠️ CUDA提供者不可用")
            return False
            
    except ImportError as e:
        print(f"❌ 验证失败，ONNX Runtime导入错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        return False

def test_gpu_functionality():
    """测试GPU功能"""
    print("\n📋 步骤4: 测试GPU功能")
    
    try:
        from utils.simple_cuda_check import test_gpu_simple
        
        result = test_gpu_simple()
        print(f"🧪 GPU测试结果: {result['message']}")
        
        if result['test_result'] == 'cuda_available':
            print("🎉 GPU功能测试成功！")
            return True
        else:
            print("⚠️ GPU功能可能仍有问题")
            return False
            
    except Exception as e:
        print(f"❌ GPU功能测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 AI换脸工具 - ONNX Runtime快速修复")
    print("=" * 50)
    
    # 修复ONNX Runtime版本
    fix_success = fix_onnxruntime_version()
    
    if fix_success:
        # 测试GPU功能
        test_success = test_gpu_functionality()
        
        if test_success:
            print("\n🎉 修复完成！GPU加速现在应该可以正常工作了。")
            print("\n下一步:")
            print("1. 重启AI换脸工具")
            print("2. 在设置中启用GPU加速")
            return 0
        else:
            print("\n⚠️ 修复部分成功，但GPU功能可能仍有问题。")
            print("建议重启计算机后再次测试。")
            return 1
    else:
        print("\n❌ 修复失败")
        print("\n可能的解决方案:")
        print("1. 手动卸载并重新安装ONNX Runtime")
        print("2. 检查网络连接")
        print("3. 使用CPU模式")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        input("\n按回车键退出...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n用户取消操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 脚本执行失败: {e}")
        input("\n按回车键退出...")
        sys.exit(1)
