#!/usr/bin/env python3
"""
使用InsightFace获取模型

这是最可靠的模型获取方式，利用InsightFace的自动下载功能。
"""

import sys
import os
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_insightface():
    """检查InsightFace是否已安装"""
    try:
        import insightface
        print("✓ InsightFace已安装")
        return True
    except ImportError:
        print("✗ InsightFace未安装")
        print("请运行: pip install insightface")
        return False

def setup_insightface_models():
    """设置InsightFace模型"""
    try:
        import insightface
        print("正在初始化InsightFace...")
        
        # 初始化FaceAnalysis，这会自动下载buffalo_l模型包
        app = insightface.app.FaceAnalysis(name='buffalo_l')
        app.prepare(ctx_id=-1, det_size=(640, 640))
        
        print("✓ InsightFace模型初始化完成")
        return True
        
    except Exception as e:
        print(f"✗ InsightFace初始化失败: {e}")
        return False

def find_insightface_models():
    """查找InsightFace下载的模型"""
    insightface_root = Path.home() / '.insightface'
    models_found = {}
    
    if not insightface_root.exists():
        print("InsightFace模型目录不存在")
        return models_found
    
    print(f"搜索InsightFace模型目录: {insightface_root}")
    
    # 需要的模型文件
    target_models = {
        'det_10g.onnx': 'scrfd_10g_bnkps.onnx',
        'det_2.5g.onnx': 'scrfd_2.5g_bnkps.onnx', 
        'rec.onnx': 'arcface_r100.onnx',
        'w600k_r50.onnx': 'w600k_r50.onnx',
        'inswapper_128.onnx': 'inswapper_128.onnx'
    }
    
    # 搜索模型文件
    for root, dirs, files in os.walk(insightface_root):
        for file in files:
            if file in target_models or file.endswith('.onnx'):
                file_path = Path(root) / file
                size_mb = file_path.stat().st_size / (1024 * 1024)
                
                # 映射到目标文件名
                target_name = target_models.get(file, file)
                models_found[target_name] = {
                    'source_path': file_path,
                    'size_mb': size_mb
                }
                
                print(f"找到模型: {file} -> {target_name} ({size_mb:.1f}MB)")
    
    return models_found

def copy_models_to_project(models_found):
    """复制模型到项目目录"""
    models_dir = PROJECT_ROOT / 'models'
    models_dir.mkdir(exist_ok=True)
    
    copied_count = 0
    
    for target_name, info in models_found.items():
        source_path = info['source_path']
        target_path = models_dir / target_name
        
        try:
            if target_path.exists():
                print(f"跳过已存在的文件: {target_name}")
                continue
            
            shutil.copy2(source_path, target_path)
            print(f"✓ 复制成功: {target_name}")
            copied_count += 1
            
        except Exception as e:
            print(f"✗ 复制失败 {target_name}: {e}")
    
    return copied_count

def download_inswapper():
    """下载InSwapper模型"""
    try:
        print("正在下载InSwapper模型...")
        from insightface.model_zoo import get_model
        
        # 这会自动下载inswapper模型
        swapper = get_model('inswapper_128.onnx', download=True, download_zip=True)
        print("✓ InSwapper模型下载完成")
        return True
        
    except Exception as e:
        print(f"✗ InSwapper下载失败: {e}")
        return False

def verify_project_models():
    """验证项目模型"""
    models_dir = PROJECT_ROOT / 'models'
    required_models = [
        'scrfd_10g_bnkps.onnx',
        'arcface_r100.onnx', 
        'inswapper_128.onnx'
    ]
    
    print(f"\n验证项目模型目录: {models_dir}")
    
    missing_models = []
    for model_name in required_models:
        model_path = models_dir / model_name
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            print(f"✓ {model_name} ({size_mb:.1f}MB)")
        else:
            print(f"✗ {model_name} (缺失)")
            missing_models.append(model_name)
    
    return len(missing_models) == 0

def main():
    """主函数"""
    print("Deep-Live-Cam InsightFace模型设置")
    print("=" * 50)
    
    # 检查InsightFace
    if not check_insightface():
        return 1
    
    # 设置InsightFace模型
    print("\n步骤1: 初始化InsightFace模型")
    if not setup_insightface_models():
        return 1
    
    # 下载InSwapper
    print("\n步骤2: 下载InSwapper模型")
    download_inswapper()
    
    # 查找模型
    print("\n步骤3: 查找已下载的模型")
    models_found = find_insightface_models()
    
    if not models_found:
        print("未找到任何模型文件")
        return 1
    
    # 复制模型
    print("\n步骤4: 复制模型到项目目录")
    copied_count = copy_models_to_project(models_found)
    
    print(f"\n复制了 {copied_count} 个模型文件")
    
    # 验证结果
    print("\n步骤5: 验证项目模型")
    if verify_project_models():
        print("\n🎉 模型设置完成！")
        print("\n下一步:")
        print("1. 运行验证: python scripts/verify_models.py")
        print("2. 测试功能: python -m dlc_batch.cli check-env")
        return 0
    else:
        print("\n⚠ 部分模型仍然缺失")
        print("请检查InsightFace安装或手动下载缺失的模型")
        return 1

if __name__ == "__main__":
    sys.exit(main())
