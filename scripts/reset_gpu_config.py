#!/usr/bin/env python3
"""
GPU配置重置工具
清除所有GPU相关配置，恢复到初始状态，用于在新电脑上重新检测GPU
"""

import sys
import json
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def reset_gpu_config():
    """重置GPU配置到初始状态"""
    print("🔄 正在重置GPU配置...")
    
    # 1. 删除GPU内存配置文件
    config_dir = project_root / "config"
    gpu_config_file = config_dir / "gpu_memory.json"
    
    if gpu_config_file.exists():
        gpu_config_file.unlink()
        print("✅ 已删除GPU内存配置文件")
    
    # 2. 清理可能的缓存目录
    cache_dirs = [
        project_root / "__pycache__",
        project_root / "core" / "__pycache__",
        project_root / "gui" / "__pycache__",
        project_root / "utils" / "__pycache__",
        project_root / "scripts" / "__pycache__"
    ]
    
    for cache_dir in cache_dirs:
        if cache_dir.exists():
            shutil.rmtree(cache_dir, ignore_errors=True)
            print(f"✅ 已清理缓存目录: {cache_dir.name}")
    
    # 3. 创建默认配置目录（如果不存在）
    config_dir.mkdir(exist_ok=True)
    
    print("\n🎯 GPU配置已重置完成！")
    print("\n📋 下次启动时将会:")
    print("   1. 重新检测GPU环境")
    print("   2. 自动选择最佳配置")
    print("   3. 可以使用傻瓜式GPU配置向导")
    
    return True

def test_gpu_detection():
    """测试GPU检测功能"""
    print("\n🔍 测试GPU检测功能...")
    
    try:
        from utils.gpu_detector import GPUDetector
        
        detector = GPUDetector()
        result = detector.detect_all()
        
        print(f"\n💻 系统: {result['system']}")
        
        # NVIDIA GPU
        nvidia = result['nvidia_gpu']
        if nvidia.get('available'):
            print(f"🎮 NVIDIA GPU: ✅ 检测到 {nvidia['count']} 个GPU")
            for gpu in nvidia['gpus']:
                print(f"   📊 {gpu['name']} ({gpu['memory_mb']}MB)")
        else:
            print("🎮 NVIDIA GPU: ❌ 未检测到")
        
        # CUDA
        cuda = result['cuda']
        if cuda.get('available'):
            print(f"🚀 CUDA: ✅ 已安装 ({cuda['version_info']})")
        else:
            print("🚀 CUDA: ❌ 未安装")
        
        # ONNX Runtime提供者
        onnx = result['onnx_providers']
        if onnx.get('available'):
            providers = onnx['providers']
            print(f"🔧 ONNX Runtime: ✅ 可用提供者: {providers}")
        else:
            print("🔧 ONNX Runtime: ❌ 不可用")
        
        # 推荐配置
        recommended = result['recommended_config']
        if recommended:
            print(f"\n🎯 推荐配置:")
            print(f"   📋 类型: {recommended['description']}")
            print(f"   🚀 提供者: {recommended['provider']}")
            print(f"   📊 性能等级: {recommended['performance']}")
            print(f"   ⚡ GPU加速: {'启用' if recommended['gpu_enabled'] else '禁用'}")
            print(f"   💡 原因: {recommended['reason']}")
        
        return True
        
    except Exception as e:
        print(f"❌ GPU检测失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🔧 GPU配置重置工具")
    print("=" * 60)
    
    # 重置配置
    if reset_gpu_config():
        # 测试检测功能
        test_gpu_detection()
        
        print("\n" + "=" * 60)
        print("✅ 重置完成！现在可以在新电脑上重新配置GPU了")
        print("💡 建议: 运行 'python scripts/one_click_gpu_setup.py' 进行自动配置")
        print("=" * 60)
    else:
        print("❌ 重置失败")
        return False
    
    return True

if __name__ == "__main__":
    main()
