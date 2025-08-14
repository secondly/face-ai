#!/usr/bin/env python3
"""
简化模型下载脚本

提供更可靠的模型下载方式，包含备用下载方案。
"""

import os
import sys
import requests
from pathlib import Path
from tqdm import tqdm

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 简化的模型配置 - 使用更可靠的源
SIMPLE_MODELS_CONFIG = {
    "inswapper_128.onnx": {
        "description": "InSwapper 换脸生成模型",
        "size_mb": 554,
        "note": "核心模型，必需"
    },
    "scrfd_10g_bnkps.onnx": {
        "description": "SCRFD 人脸检测模型 (高精度)",
        "size_mb": 16.9,
        "note": "推荐使用"
    },
    "arcface_r100.onnx": {
        "description": "ArcFace 人脸识别模型",
        "size_mb": 248,
        "note": "核心模型，必需"
    }
}

def download_file_with_requests(url, file_path, description):
    """使用requests下载文件"""
    try:
        print(f"正在下载: {description}")
        print(f"URL: {url}")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(file_path, 'wb') as f, tqdm(
            desc=description,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        print(f"✓ 下载完成: {file_path}")
        return True
        
    except Exception as e:
        print(f"✗ 下载失败: {e}")
        return False

def show_manual_download_instructions():
    """显示手动下载说明"""
    print("\n" + "="*60)
    print("自动下载失败，请手动下载模型文件")
    print("="*60)
    
    models_dir = PROJECT_ROOT / "models"
    models_dir.mkdir(exist_ok=True)
    
    print(f"\n模型保存目录: {models_dir}")
    print("\n请下载以下模型文件:")
    
    manual_links = {
        "inswapper_128.onnx": [
            "https://github.com/facefusion/facefusion-assets/releases/download/models/inswapper_128.onnx",
            "https://huggingface.co/deepinsight/inswapper/resolve/main/inswapper_128.onnx"
        ],
        "scrfd_10g_bnkps.onnx": [
            "https://github.com/facefusion/facefusion-assets/releases/download/models/scrfd_10g_bnkps.onnx"
        ],
        "arcface_r100.onnx": [
            "https://github.com/facefusion/facefusion-assets/releases/download/models/arcface_r100.onnx"
        ]
    }
    
    for i, (model_name, config) in enumerate(SIMPLE_MODELS_CONFIG.items(), 1):
        print(f"\n{i}. {model_name}")
        print(f"   描述: {config['description']}")
        print(f"   大小: {config['size_mb']} MB")
        print(f"   备注: {config['note']}")
        
        if model_name in manual_links:
            print("   下载链接:")
            for j, link in enumerate(manual_links[model_name], 1):
                print(f"     {j}. {link}")
    
    print(f"\n下载完成后，请将文件放置到: {models_dir}")
    print("然后运行验证脚本: python scripts/verify_models.py")

def check_existing_models():
    """检查已存在的模型"""
    models_dir = PROJECT_ROOT / "models"
    existing_models = []
    missing_models = []
    
    for model_name in SIMPLE_MODELS_CONFIG.keys():
        model_path = models_dir / model_name
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            existing_models.append((model_name, size_mb))
        else:
            missing_models.append(model_name)
    
    if existing_models:
        print("已存在的模型:")
        for model_name, size_mb in existing_models:
            print(f"  ✓ {model_name} ({size_mb:.1f} MB)")
    
    if missing_models:
        print("缺失的模型:")
        for model_name in missing_models:
            config = SIMPLE_MODELS_CONFIG[model_name]
            print(f"  ✗ {model_name} - {config['description']} ({config['size_mb']} MB)")
    
    return existing_models, missing_models

def create_models_directory():
    """创建模型目录"""
    models_dir = PROJECT_ROOT / "models"
    models_dir.mkdir(exist_ok=True)
    print(f"模型目录: {models_dir}")
    return models_dir

def main():
    """主函数"""
    print("Deep-Live-Cam 简化模型下载器")
    print("="*50)
    
    # 创建模型目录
    models_dir = create_models_directory()
    
    # 检查现有模型
    existing_models, missing_models = check_existing_models()
    
    if not missing_models:
        print("\n✓ 所有核心模型都已存在")
        print("运行验证脚本: python scripts/verify_models.py")
        return
    
    print(f"\n需要下载 {len(missing_models)} 个模型")
    
    # 尝试自动下载 (这里可以添加实际的下载逻辑)
    print("\n注意: 由于模型文件较大且下载源可能不稳定，")
    print("建议使用以下方式获取模型:")
    
    print("\n方式1: 使用InsightFace自动下载 (推荐)")
    print("运行以下Python代码:")
    print("""
import insightface
app = insightface.app.FaceAnalysis(name='buffalo_l')
app.prepare(ctx_id=0, det_size=(640, 640))
# 这将自动下载所需的模型到 ~/.insightface/models/
""")
    
    print("\n方式2: 手动下载")
    show_manual_download_instructions()
    
    print("\n方式3: 使用其他工具")
    print("- 使用git-lfs克隆模型仓库")
    print("- 使用huggingface-hub下载")
    print("- 使用wget或curl命令行工具")
    
    print("\n完成下载后，运行验证脚本:")
    print("python scripts/verify_models.py")

if __name__ == "__main__":
    main()
