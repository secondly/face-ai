#!/usr/bin/env python3
"""
简化的模型获取器 - 一个脚本解决所有问题
专注于可靠性，不追求复杂功能
"""

import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path


def install_package(package_name):
    """安装Python包"""
    print(f"正在安装 {package_name}...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package_name
        ], check=True, capture_output=True, text=True, timeout=300)
        print(f"✅ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package_name} 安装失败: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print(f"❌ {package_name} 安装超时")
        return False


def download_with_requests(url, file_path):
    """使用requests下载文件"""
    try:
        import requests
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"正在下载: {url}")
        response = requests.get(url, headers=headers, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded * 100) // total_size
                        print(f"\r进度: {percent}%", end="")
        
        print(f"\n✅ 下载完成: {file_path.name}")
        return True
        
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        return False


def download_inswapper():
    """下载InSwapper模型"""
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    inswapper_path = models_dir / "inswapper_128.onnx"
    
    if inswapper_path.exists():
        print("✅ inswapper_128.onnx 已存在")
        return True
    
    # Civitai链接
    url = "https://civitai.com/api/download/models/85159"
    
    print("📥 下载 InSwapper 模型...")
    return download_with_requests(url, inswapper_path)


def setup_insightface_and_download():
    """设置InsightFace并下载其他模型"""
    print("\n📦 设置InsightFace环境...")
    
    # 1. 安装必要的依赖
    packages = ["onnxruntime", "insightface"]
    for package in packages:
        if not install_package(package):
            return False
    
    # 2. 下载InsightFace模型
    try:
        print("📥 下载InsightFace模型...")
        
        import insightface
        from insightface.model_zoo import get_model
        
        # 下载buffalo_l模型包
        print("正在下载buffalo_l模型包...")
        app = insightface.app.FaceAnalysis(name='buffalo_l')
        app.prepare(ctx_id=-1, det_size=(640, 640))
        print("✅ buffalo_l模型包下载完成")
        
        # 下载inswapper模型 (如果还没有)
        models_dir = Path("models")
        inswapper_path = models_dir / "inswapper_128.onnx"
        if not inswapper_path.exists():
            print("正在下载inswapper模型...")
            swapper = get_model('inswapper_128.onnx', download=True, download_zip=True)
            print("✅ inswapper模型下载完成")
        
        return True
        
    except Exception as e:
        print(f"❌ InsightFace下载失败: {e}")
        return False


def copy_insightface_models():
    """从InsightFace目录复制模型到项目"""
    print("\n📋 复制InsightFace模型到项目...")
    
    insightface_root = Path.home() / '.insightface'
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # 文件映射 - 根据实际InsightFace buffalo_l模型包内容
    file_mapping = {
        'scrfd_10g_bnkps.onnx': ['det_10g.onnx'],
        'arcface_r100.onnx': ['w600k_r50.onnx'],  # buffalo_l中的识别模型
        'inswapper_128.onnx': ['inswapper_128.onnx']
    }
    
    success_count = 0
    
    for target_name, source_names in file_mapping.items():
        target_path = models_dir / target_name
        
        if target_path.exists():
            print(f"✅ {target_name} 已存在")
            success_count += 1
            continue
        
        # 搜索源文件
        found = False
        for root, dirs, files in os.walk(insightface_root):
            for source_name in source_names:
                if source_name in files:
                    source_path = Path(root) / source_name
                    try:
                        shutil.copy2(source_path, target_path)
                        print(f"✅ 复制 {source_name} -> {target_name}")
                        success_count += 1
                        found = True
                        break
                    except Exception as e:
                        print(f"❌ 复制失败: {e}")
            if found:
                break
        
        if not found:
            print(f"⚠️ 未找到 {target_name}")
    
    return success_count


def check_models():
    """检查模型状态"""
    models_dir = Path("models")
    required_models = [
        "inswapper_128.onnx",      # 换脸生成模型
        "scrfd_10g_bnkps.onnx",    # 人脸检测模型
        "arcface_r100.onnx"        # 人脸识别模型 (从w600k_r50.onnx复制)
    ]
    
    print("\n📋 检查模型状态:")
    existing_count = 0
    
    for model_name in required_models:
        model_path = models_dir / model_name
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            print(f"✅ {model_name} ({size_mb:.1f} MB)")
            existing_count += 1
        else:
            print(f"❌ {model_name} 缺失")
    
    return existing_count, len(required_models)


def main():
    """主函数"""
    print("🎭 简化模型获取器")
    print("=" * 40)
    
    # 检查当前状态
    existing, total = check_models()
    
    if existing == total:
        print(f"\n🎉 所有模型都已存在 ({existing}/{total})")
        print("✅ 您可以开始使用AI换脸功能了！")
        return
    
    print(f"\n🔄 需要获取 {total - existing} 个模型")
    
    # 1. 先尝试下载InSwapper (最容易成功的)
    print("\n=== 步骤1: 下载InSwapper模型 ===")
    if not download_inswapper():
        print("⚠️ InSwapper下载失败，但继续尝试其他模型...")
    
    # 2. 设置InsightFace并下载其他模型
    print("\n=== 步骤2: 设置InsightFace ===")
    if setup_insightface_and_download():
        # 3. 复制模型到项目
        print("\n=== 步骤3: 复制模型到项目 ===")
        copy_insightface_models()
    else:
        print("⚠️ InsightFace设置失败")
    
    # 4. 最终检查
    print("\n=== 最终结果 ===")
    final_existing, final_total = check_models()
    
    if final_existing == final_total:
        print(f"\n🎉 所有模型获取成功！({final_existing}/{final_total})")
        print("✅ 您现在可以开始使用AI换脸功能了")
        print("💡 运行: python main.py --help 查看使用方法")
    elif final_existing >= 2:  # 至少有2个核心模型
        print(f"\n⚠️ 部分模型获取成功 ({final_existing}/{final_total})")
        print("✅ 基本功能可以使用")
        print("💡 如需完整功能，请重新运行此脚本或手动下载缺失模型")
    else:
        print(f"\n❌ 模型获取失败 ({final_existing}/{final_total})")
        print("🔧 建议:")
        print("1. 检查网络连接")
        print("2. 手动安装: pip install onnxruntime insightface")
        print("3. 重新运行此脚本")
        print("4. 查看详细指导: 模型获取指南.md")


if __name__ == "__main__":
    main()
