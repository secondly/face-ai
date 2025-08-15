#!/usr/bin/env python3
"""
新电脑验证脚本
验证程序在新电脑上的运行状态，特别是GPU配置
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """检查依赖包"""
    print("📦 检查Python依赖包...")
    
    required_packages = [
        'cv2',
        'numpy', 
        'PyQt5',
        'onnxruntime',
        'insightface'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'cv2':
                import cv2
                print(f"   ✅ OpenCV: {cv2.__version__}")
            elif package == 'numpy':
                import numpy as np
                print(f"   ✅ NumPy: {np.__version__}")
            elif package == 'PyQt5':
                from PyQt5.QtCore import QT_VERSION_STR
                print(f"   ✅ PyQt5: {QT_VERSION_STR}")
            elif package == 'onnxruntime':
                import onnxruntime as ort
                print(f"   ✅ ONNX Runtime: {ort.__version__}")
            elif package == 'insightface':
                import insightface
                print(f"   ✅ InsightFace: {insightface.__version__}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package}: 未安装")
    
    return len(missing_packages) == 0, missing_packages

def check_models():
    """检查模型文件"""
    print("\n🤖 检查AI模型文件...")
    
    models_dir = project_root / "models"
    required_models = [
        "inswapper_128.onnx",
        "arcface_r100.onnx", 
        "scrfd_10g_bnkps.onnx"
    ]
    
    missing_models = []
    
    for model in required_models:
        model_path = models_dir / model
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ {model}: {size_mb:.1f}MB")
        else:
            missing_models.append(model)
            print(f"   ❌ {model}: 文件不存在")
    
    return len(missing_models) == 0, missing_models

def check_ffmpeg():
    """检查FFmpeg"""
    print("\n🎬 检查FFmpeg...")
    
    ffmpeg_dir = project_root / "ffmpeg"
    ffmpeg_exe = ffmpeg_dir / "ffmpeg.exe"
    
    if ffmpeg_exe.exists():
        print(f"   ✅ FFmpeg: {ffmpeg_exe}")
        return True
    else:
        print(f"   ❌ FFmpeg: 未找到")
        return False

def check_gpu_config():
    """检查GPU配置"""
    print("\n🎮 检查GPU配置...")
    
    try:
        from utils.gpu_detector import GPUDetector
        
        detector = GPUDetector()
        result = detector.detect_all()
        
        print(f"   💻 系统: {result['system']}")
        
        # GPU状态
        gpu_available = result.get('gpu_available', False)
        if gpu_available:
            recommended = result['recommended_config']
            print(f"   ✅ GPU加速: 可用")
            print(f"   🚀 推荐配置: {recommended['description']}")
            print(f"   📊 性能等级: {recommended['performance']}")
        else:
            print(f"   ❌ GPU加速: 不可用，将使用CPU模式")
        
        return True, gpu_available
        
    except Exception as e:
        print(f"   ❌ GPU检测失败: {e}")
        return False, False

def test_core_functionality():
    """测试核心功能"""
    print("\n🧪 测试核心功能...")
    
    try:
        from core.face_swapper import FaceSwapper
        
        # 创建FaceSwapper实例（不初始化模型）
        print("   🔧 创建FaceSwapper实例...")
        swapper = FaceSwapper(use_gpu=False)  # 先用CPU测试
        
        print("   ✅ 核心功能正常")
        return True
        
    except Exception as e:
        print(f"   ❌ 核心功能测试失败: {e}")
        return False

def generate_report(deps_ok, models_ok, ffmpeg_ok, gpu_ok, gpu_available, core_ok):
    """生成验证报告"""
    print("\n" + "=" * 60)
    print("📋 新电脑验证报告")
    print("=" * 60)
    
    overall_status = all([deps_ok, models_ok, ffmpeg_ok, gpu_ok, core_ok])
    
    print(f"📦 Python依赖: {'✅ 正常' if deps_ok else '❌ 缺失'}")
    print(f"🤖 AI模型文件: {'✅ 完整' if models_ok else '❌ 缺失'}")
    print(f"🎬 FFmpeg工具: {'✅ 可用' if ffmpeg_ok else '❌ 缺失'}")
    print(f"🎮 GPU检测: {'✅ 正常' if gpu_ok else '❌ 失败'}")
    print(f"⚡ GPU加速: {'✅ 可用' if gpu_available else '❌ 不可用 (将使用CPU)'}")
    print(f"🧪 核心功能: {'✅ 正常' if core_ok else '❌ 异常'}")
    
    print(f"\n🎯 总体状态: {'✅ 可以正常使用' if overall_status else '❌ 需要修复问题'}")
    
    if not overall_status:
        print("\n💡 修复建议:")
        if not deps_ok:
            print("   📦 运行: pip install -r requirements.txt")
        if not models_ok:
            print("   🤖 运行: python scripts/download_models.py")
        if not ffmpeg_ok:
            print("   🎬 运行: python download_ffmpeg.py")
        if not gpu_ok:
            print("   🎮 检查GPU驱动和ONNX Runtime安装")
    
    if gpu_available:
        print("\n🚀 GPU加速可用！建议运行:")
        print("   python scripts/one_click_gpu_setup.py")
    
    return overall_status

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 新电脑环境验证")
    print("=" * 60)
    print("正在检查程序在新电脑上的运行环境...\n")
    
    # 执行各项检查
    deps_ok, missing_deps = check_dependencies()
    models_ok, missing_models = check_models()
    ffmpeg_ok = check_ffmpeg()
    gpu_ok, gpu_available = check_gpu_config()
    core_ok = test_core_functionality()
    
    # 生成报告
    overall_ok = generate_report(deps_ok, models_ok, ffmpeg_ok, gpu_ok, gpu_available, core_ok)
    
    print("\n" + "=" * 60)
    if overall_ok:
        print("🎉 验证完成！程序可以在新电脑上正常运行")
    else:
        print("⚠️  验证发现问题，请按照建议进行修复")
    print("=" * 60)
    
    return overall_ok

if __name__ == "__main__":
    main()
