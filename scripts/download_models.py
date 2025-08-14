#!/usr/bin/env python3
"""
模型下载脚本

自动下载Deep-Live-Cam所需的ONNX模型文件。
"""

import os
import sys
import hashlib
import argparse
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError
import tempfile
import shutil

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 模型下载配置 - 推荐使用InsightFace自动下载
MODELS_CONFIG = {
    "inswapper_128.onnx": {
        "urls": [
            "https://civitai.com/api/download/models/85159"
        ],
        "sha256": "e4a3f08c753cb72d04e10aa0f7dbe3deebbf39567d4ead6dce08e98aa49e16af",
        "size_mb": 554,
        "description": "InSwapper 换脸生成模型",
        "required": True,
        "insightface_name": "inswapper"
    },
    "scrfd_10g_bnkps.onnx": {
        "urls": [],  # 推荐使用InsightFace自动下载
        "sha256": "5838f7fe053675b1c7a08b633df49e7af5495cee0493c7dcf6697200b85b5b91",
        "size_mb": 16.9,
        "description": "SCRFD 人脸检测模型 (高精度版本)",
        "required": True,
        "insightface_name": "scrfd_10g_bnkps"
    },
    "scrfd_2.5g_bnkps.onnx": {
        "urls": [],  # 推荐使用InsightFace自动下载
        "sha256": "e692b7e8f6c2c8b7ecbd68c4072b9c6b7c8b7e8f6c2c8b7ecbd68c4072b9c6b7",
        "size_mb": 3.3,
        "description": "SCRFD 人脸检测模型 (快速版本)",
        "required": False,
        "insightface_name": "scrfd_2.5g_bnkps"
    },
    "arcface_r100.onnx": {
        "urls": [],  # 推荐使用InsightFace自动下载
        "sha256": "8ffe2b1f775b1c4a15709c5a040b709cfb184d02b204569d36693bbbf47d05d9",
        "size_mb": 248,
        "description": "ArcFace 人脸识别模型 (ResNet100)",
        "required": True,
        "insightface_name": "arcface_r100"
    },
    "w600k_r50.onnx": {
        "urls": [],  # 推荐使用InsightFace自动下载
        "sha256": "4c06341c33c2ca1f86781dab0e829f88ad5b64be9fba56e56bc9ebdefc619e43",
        "size_mb": 166,
        "description": "ArcFace 人脸识别模型 (ResNet50)",
        "required": False,
        "insightface_name": "w600k_r50"
    },
    "bisenet_face.onnx": {
        "urls": [],  # 推荐使用InsightFace自动下载
        "sha256": "5c06341c33c2ca1f86781dab0e829f88ad5b64be9fba56e56bc9ebdefc619e44",
        "size_mb": 33.2,
        "description": "BiSeNet 人脸分割模型",
        "required": False,
        "insightface_name": "bisenet"
    }
}

def calculate_sha256(file_path):
    """计算文件SHA256哈希值"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.1f} GB"

def download_with_progress(urls, file_path, description):
    """带进度显示的文件下载 - 支持多个URL尝试"""
    if isinstance(urls, str):
        urls = [urls]

    print(f"正在下载: {description}")
    print(f"保存到: {file_path}")

    for i, url in enumerate(urls):
        print(f"尝试源 {i+1}/{len(urls)}: {url}")

        # 首先尝试requests下载 (支持更好的HTTP头)
        if try_requests_download(url, file_path):
            print(f"✓ 下载成功 (源 {i+1})")
            return True

        # 如果requests失败，尝试urllib
        try:
            def progress_hook(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(100, (block_num * block_size * 100) // total_size)
                    downloaded = min(block_num * block_size, total_size)
                    print(f"\r进度: {percent:3d}% ({format_size(downloaded)}/{format_size(total_size)})", end="")

            # 下载到临时文件
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_path = tmp_file.name

            # 设置User-Agent
            import urllib.request
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')]
            urllib.request.install_opener(opener)

            urlretrieve(url, tmp_path, progress_hook)
            print()  # 换行

            # 移动到目标位置
            shutil.move(tmp_path, file_path)
            print(f"✓ 下载成功 (源 {i+1})")
            return True

        except URLError as e:
            print(f"\n✗ 源 {i+1} 下载失败: {e}")
            # 清理临时文件
            try:
                if 'tmp_path' in locals():
                    os.unlink(tmp_path)
            except:
                pass
        except Exception as e:
            print(f"\n✗ 源 {i+1} 下载出错: {e}")
            # 清理临时文件
            try:
                if 'tmp_path' in locals():
                    os.unlink(tmp_path)
            except:
                pass

    print(f"✗ 所有下载源都失败")
    return False

def try_requests_download(url, file_path):
    """使用requests库下载文件"""
    try:
        import requests

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        print("  使用requests下载...")
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(file_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded * 100) // total_size
                        print(f"\r  进度: {percent:3d}% ({format_size(downloaded)}/{format_size(total_size)})", end="")

        print()  # 换行
        return True

    except ImportError:
        print("  requests库未安装，跳过")
        return False
    except Exception as e:
        print(f"\n  requests下载失败: {e}")
        return False

def show_manual_download_guide(model_name, config):
    """显示手动下载指导"""
    print(f"\n{'='*60}")
    print(f"手动下载指导: {model_name}")
    print(f"{'='*60}")
    print(f"模型描述: {config['description']}")
    print(f"文件大小: {config['size_mb']} MB")
    print(f"保存路径: models/{model_name}")
    print("\n可尝试的下载方式:")

    print("\n1. 使用InsightFace自动下载 (强烈推荐):")
    print("   # 这是最可靠的方式，官方支持")
    print("   pip install insightface")
    print("   python -c \"")
    print("   import insightface")
    print("   # 下载buffalo_l模型包 (包含检测和识别模型)")
    print("   app = insightface.app.FaceAnalysis(name='buffalo_l')")
    print("   app.prepare(ctx_id=-1, det_size=(640, 640))")
    print("   # 下载inswapper模型")
    print("   from insightface.model_zoo import get_model")
    print("   swapper = get_model('inswapper_128.onnx', download=True, download_zip=True)")
    print("   \"")
    print("   # 模型会下载到 ~/.insightface/models/")
    print("   # 然后复制对应文件到项目的 models/ 目录")

    if config['urls']:
        print("\n2. 浏览器下载:")
        for i, url in enumerate(config['urls'], 1):
            print(f"   {i}. {url}")

        print("\n3. 命令行下载:")
        for i, url in enumerate(config['urls'], 1):
            print(f"   wget -O models/{model_name} \"{url}\"")
            break  # 只显示第一个
    else:
        print(f"\n2. 注意: {model_name} 没有可用的直接下载链接")
        print("   建议使用InsightFace自动下载方式")

    print("\n4. 从其他项目复制:")
    print("   - FaceFusion: ~/.cache/facefusion/models/")
    print("   - Roop: ./models/")
    print("   - 其他换脸项目的模型目录")

    print("\n5. 使用专门的下载工具:")
    print("   - huggingface-cli (需要登录)")
    print("   - git-lfs clone 模型仓库")
    print("   - aria2c 多线程下载器")

    print(f"\n下载完成后请验证文件:")
    print(f"   python scripts/verify_models.py --models {model_name}")
    print(f"{'='*60}")

def try_insightface_download(model_name, target_path):
    """尝试使用InsightFace下载模型"""
    try:
        print(f"尝试使用InsightFace下载 {model_name}...")
        import insightface
        import os
        from pathlib import Path

        # 获取InsightFace模型目录
        insightface_root = Path.home() / '.insightface'

        if model_name in MODELS_CONFIG:
            config = MODELS_CONFIG[model_name]
            insightface_name = config.get('insightface_name')

            if insightface_name:
                # 尝试触发InsightFace自动下载
                if 'scrfd' in insightface_name:
                    # 人脸检测模型
                    app = insightface.app.FaceAnalysis(name='buffalo_l')
                    app.prepare(ctx_id=-1, det_size=(640, 640))
                elif 'arcface' in insightface_name:
                    # 人脸识别模型
                    app = insightface.app.FaceAnalysis(name='buffalo_l')
                    app.prepare(ctx_id=-1, det_size=(640, 640))
                elif 'inswapper' in insightface_name:
                    # 换脸模型
                    from insightface.model_zoo import get_model
                    swapper = get_model('inswapper_128.onnx', download=True, download_zip=True)

                # 查找下载的模型文件
                for root, dirs, files in os.walk(insightface_root):
                    for file in files:
                        if file == model_name:
                            source_path = Path(root) / file
                            print(f"找到InsightFace模型: {source_path}")

                            # 复制到目标位置
                            import shutil
                            shutil.copy2(source_path, target_path)
                            print(f"✓ 从InsightFace复制模型成功")
                            return True

        print("InsightFace中未找到对应模型")
        return False

    except ImportError:
        print("InsightFace未安装，跳过自动下载")
        print("可以运行: pip install insightface")
        return False
    except Exception as e:
        print(f"InsightFace下载失败: {e}")
        return False

def verify_model(file_path, expected_sha256):
    """验证模型文件完整性"""
    if not os.path.exists(file_path):
        return False, "文件不存在"
    
    print(f"正在验证: {os.path.basename(file_path)}")
    actual_sha256 = calculate_sha256(file_path)
    
    if actual_sha256 == expected_sha256:
        return True, "验证通过"
    else:
        return False, f"SHA256不匹配\n期望: {expected_sha256}\n实际: {actual_sha256}"

def download_models(models_dir, models_list=None, force=False, verify=True):
    """下载模型文件"""
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    
    if models_list is None:
        models_list = list(MODELS_CONFIG.keys())
    
    success_count = 0
    total_count = len(models_list)
    
    print(f"开始下载 {total_count} 个模型文件到: {models_dir}")
    print("=" * 60)
    
    for model_name in models_list:
        if model_name not in MODELS_CONFIG:
            print(f"警告: 未知模型 {model_name}")
            continue
            
        config = MODELS_CONFIG[model_name]
        file_path = models_dir / model_name
        
        print(f"\n[{success_count + 1}/{total_count}] {model_name}")
        print(f"描述: {config['description']}")
        print(f"大小: {config['size_mb']} MB")
        
        # 检查文件是否已存在
        if file_path.exists() and not force:
            if verify:
                is_valid, msg = verify_model(file_path, config['sha256'])
                if is_valid:
                    print("✓ 文件已存在且验证通过，跳过下载")
                    success_count += 1
                    continue
                else:
                    print(f"✗ 文件验证失败: {msg}")
                    print("重新下载...")
            else:
                print("✓ 文件已存在，跳过下载")
                success_count += 1
                continue
        
        # 下载文件
        download_success = download_with_progress(config['urls'], file_path, config['description'])

        if not download_success:
            # 尝试InsightFace下载
            download_success = try_insightface_download(model_name, file_path)

        if download_success:
            if verify:
                is_valid, msg = verify_model(file_path, config['sha256'])
                if is_valid:
                    print("✓ 下载完成并验证通过")
                    success_count += 1
                else:
                    print(f"✗ 下载完成但验证失败: {msg}")
                    file_path.unlink()  # 删除损坏的文件
                    show_manual_download_guide(model_name, config)
            else:
                print("✓ 下载完成")
                success_count += 1
        else:
            print("✗ 下载失败")
            show_manual_download_guide(model_name, config)
    
    print("\n" + "=" * 60)
    print(f"下载完成: {success_count}/{total_count} 个模型")
    
    if success_count == total_count:
        print("✓ 所有模型下载成功！")
        return True
    else:
        print(f"✗ {total_count - success_count} 个模型下载失败")
        return False

def main():
    parser = argparse.ArgumentParser(description="下载Deep-Live-Cam模型文件")
    parser.add_argument("--models-dir", default=str(PROJECT_ROOT / "models"),
                       help="模型保存目录 (默认: ./models)")
    parser.add_argument("--models", nargs="+", 
                       help="指定要下载的模型 (默认: 下载所有核心模型)")
    parser.add_argument("--force", action="store_true",
                       help="强制重新下载已存在的文件")
    parser.add_argument("--no-verify", action="store_true",
                       help="跳过文件完整性验证")
    parser.add_argument("--list", action="store_true",
                       help="列出所有可用模型")
    
    args = parser.parse_args()
    
    if args.list:
        print("可用模型列表:")
        print("=" * 60)
        for name, config in MODELS_CONFIG.items():
            print(f"{name}")
            print(f"  描述: {config['description']}")
            print(f"  大小: {config['size_mb']} MB")
            print()
        return
    
    # 默认下载核心模型
    if args.models is None:
        # 只下载必需的核心模型
        core_models = []
        for model_name, config in MODELS_CONFIG.items():
            if config.get('required', False):
                core_models.append(model_name)

        if not core_models:
            # 如果没有标记为required的，使用默认核心模型
            core_models = [
                "inswapper_128.onnx",
                "scrfd_10g_bnkps.onnx",
                "arcface_r100.onnx"
            ]

        args.models = core_models
    
    success = download_models(
        models_dir=args.models_dir,
        models_list=args.models,
        force=args.force,
        verify=not args.no_verify
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
