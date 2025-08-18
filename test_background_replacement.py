#!/usr/bin/env python3
"""
测试背景替换功能
"""

import cv2
import numpy as np
from pathlib import Path
import sys
import os

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_background_replacer():
    """测试背景替换器"""
    try:
        from core.background_replacer import BackgroundReplacer
        
        print("🎨 测试背景替换功能")
        print("=" * 50)
        
        # 测试不同的模式
        modes = ["rembg", "u2net", "modnet", "backgroundmattingv2"]
        
        for mode in modes:
            print(f"\n📝 测试模式: {mode}")
            try:
                replacer = BackgroundReplacer(mode=mode)
                if replacer.is_available():
                    print(f"✅ {mode} 模式初始化成功")
                else:
                    print(f"❌ {mode} 模式初始化失败")
            except Exception as e:
                print(f"❌ {mode} 模式出错: {e}")
        
        # 创建测试图像
        print("\n🖼️ 创建测试图像...")
        test_image = create_test_image()
        background_image = create_test_background()
        
        # 测试背景替换
        print("\n🔄 测试背景替换...")
        try:
            replacer = BackgroundReplacer(mode="rembg")
            if replacer.is_available():
                result = replacer.replace_background(test_image, background_image)
                if result is not None:
                    print("✅ 背景替换测试成功")
                    
                    # 保存测试结果
                    output_dir = Path("test_results")
                    output_dir.mkdir(exist_ok=True)
                    
                    cv2.imwrite(str(output_dir / "test_original.jpg"), test_image)
                    cv2.imwrite(str(output_dir / "test_background.jpg"), background_image)
                    cv2.imwrite(str(output_dir / "test_result.jpg"), result)
                    
                    print(f"📁 测试结果保存到: {output_dir.absolute()}")
                else:
                    print("❌ 背景替换返回None")
            else:
                print("❌ 背景替换器不可用")
        except Exception as e:
            print(f"❌ 背景替换测试失败: {e}")
        
    except ImportError as e:
        print(f"❌ 导入背景替换模块失败: {e}")
        print("💡 请先安装依赖: python scripts/install_background_deps.py")

def create_test_image():
    """创建测试图像（模拟人像）"""
    # 创建一个简单的测试图像
    image = np.zeros((400, 300, 3), dtype=np.uint8)
    
    # 添加背景色
    image[:] = (100, 150, 200)  # 浅蓝色背景
    
    # 添加一个简单的"人像"（圆形）
    center = (150, 200)
    radius = 80
    cv2.circle(image, center, radius, (180, 120, 80), -1)  # 肤色圆形
    
    # 添加"眼睛"
    cv2.circle(image, (130, 180), 8, (0, 0, 0), -1)
    cv2.circle(image, (170, 180), 8, (0, 0, 0), -1)
    
    # 添加"嘴巴"
    cv2.ellipse(image, (150, 220), (20, 10), 0, 0, 180, (0, 0, 0), 2)
    
    return image

def create_test_background():
    """创建测试背景图像"""
    # 创建渐变背景
    background = np.zeros((400, 300, 3), dtype=np.uint8)
    
    for y in range(400):
        for x in range(300):
            # 创建彩虹渐变
            r = int(255 * (x / 300))
            g = int(255 * (y / 400))
            b = int(255 * ((x + y) / 700))
            background[y, x] = (b, g, r)  # BGR格式
    
    return background

def check_dependencies():
    """检查依赖是否安装"""
    print("🔍 检查依赖...")
    
    dependencies = [
        ("cv2", "opencv-python"),
        ("numpy", "numpy"),
        ("PIL", "Pillow"),
    ]
    
    optional_deps = [
        ("rembg", "rembg[new]"),
        ("torch", "torch"),
    ]
    
    all_good = True
    
    for module, package in dependencies:
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - 请安装: pip install {package}")
            all_good = False
    
    print("\n📦 可选依赖 (背景替换功能):")
    for module, package in optional_deps:
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"⚠️ {package} - 可选: pip install {package}")
    
    return all_good

def main():
    """主函数"""
    print("🧪 AI换脸 - 背景替换功能测试")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 缺少必要依赖，请先安装")
        return
    
    # 测试背景替换
    test_background_replacer()
    
    print("\n" + "=" * 60)
    print("🎉 测试完成！")
    print("\n💡 使用说明:")
    print("1. 在GUI中勾选'启用背景替换'")
    print("2. 选择背景替换模式")
    print("3. 选择背景图片或背景文件夹")
    print("4. 开始换脸处理")
    
    print("\n📚 支持的模式:")
    print("• Rembg (推荐) - 简单易用，效果好")
    print("• U2Net - 通用目标分割")
    print("• MODNet - 快速人像分割")
    print("• BackgroundMattingV2 - 高质量背景替换")

if __name__ == "__main__":
    main()
