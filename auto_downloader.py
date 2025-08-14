"""
自动下载器 - 下载必要的模型文件和工具
使用InsightFace官方方式下载模型，确保可靠性
"""

import os
import json
import hashlib
import zipfile
import requests
import platform
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Callable
import logging

logger = logging.getLogger(__name__)

class AutoDownloader:
    """自动下载器类"""

    def __init__(self, config_file: str = "download_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.models_dir = Path("models")
        self.ffmpeg_dir = Path("ffmpeg")

        # 创建目录
        self.models_dir.mkdir(exist_ok=True)
        self.ffmpeg_dir.mkdir(exist_ok=True)
    
    def _load_config(self) -> Dict:
        """加载下载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}
    
    def _download_file(self, url: str, filepath: Path, 
                      progress_callback: Optional[Callable] = None) -> bool:
        """下载文件"""
        try:
            logger.info(f"开始下载: {url}")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(f"下载中... {progress:.1f}%", progress)
            
            logger.info(f"下载完成: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"下载失败 {url}: {e}")
            if filepath.exists():
                filepath.unlink()
            return False
    
    def _verify_file(self, filepath: Path, expected_md5: str = None) -> bool:
        """验证文件完整性"""
        if not filepath.exists():
            return False
        
        if expected_md5:
            try:
                with open(filepath, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                return file_hash == expected_md5
            except Exception as e:
                logger.error(f"文件验证失败 {filepath}: {e}")
                return False
        
        return True
    
    def _install_package(self, package_name: str, progress_callback: Optional[Callable] = None, base_progress: float = 0) -> bool:
        """安装Python包"""
        try:
            logger.info(f"正在安装 {package_name}...")
            if progress_callback:
                progress_callback(f"正在安装 {package_name}...", base_progress)

            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package_name, "--progress-bar", "off"
            ], check=True, capture_output=True, text=True, timeout=300)

            logger.info(f"✅ {package_name} 安装成功")
            if progress_callback:
                progress_callback(f"✅ {package_name} 安装完成", base_progress + 2)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ {package_name} 安装失败: {e.stderr}")
            if progress_callback:
                progress_callback(f"❌ {package_name} 安装失败", base_progress)
            return False
        except subprocess.TimeoutExpired:
            logger.error(f"❌ {package_name} 安装超时")
            if progress_callback:
                progress_callback(f"❌ {package_name} 安装超时", base_progress)
            return False
        except subprocess.TimeoutExpired:
            logger.error(f"❌ {package_name} 安装超时")
            return False

    def _download_inswapper_from_civitai(self, progress_callback: Optional[Callable] = None) -> bool:
        """从Civitai下载InSwapper模型"""
        inswapper_path = self.models_dir / "inswapper_128.onnx"

        if inswapper_path.exists():
            logger.info("✅ inswapper_128.onnx 已存在")
            return True

        # Civitai链接 - 这个是有效的
        url = "https://civitai.com/api/download/models/85159"

        if progress_callback:
            progress_callback("正在下载 InSwapper 模型...", 10)

        logger.info("📥 下载 InSwapper 模型...")
        return self._download_file(url, inswapper_path, progress_callback)

    def _setup_insightface_models(self, progress_callback: Optional[Callable] = None) -> bool:
        """使用InsightFace下载其他模型"""
        try:
            if progress_callback:
                progress_callback("正在安装InsightFace...", 20)

            # 1. 安装必要的依赖
            packages = ["onnxruntime", "insightface"]
            for i, package in enumerate(packages):
                base_progress = 20 + (i * 5)
                if not self._install_package(package, progress_callback, base_progress):
                    return False

            if progress_callback:
                progress_callback("正在下载InsightFace模型包...", 30)

            # 2. 下载InsightFace模型
            logger.info("📥 下载InsightFace模型...")

            import insightface
            from insightface.model_zoo import get_model

            # 下载buffalo_l模型包 - 分步显示进度
            if progress_callback:
                progress_callback("正在初始化buffalo_l模型...", 35)

            logger.info("正在下载buffalo_l模型包...")

            # 创建模拟进度更新
            import threading
            import time

            download_complete = threading.Event()

            def simulate_progress():
                """模拟下载进度"""
                progress = 35
                while not download_complete.is_set() and progress < 55:
                    time.sleep(2)  # 每2秒更新一次
                    progress += 2
                    if progress_callback:
                        progress_callback(f"正在下载buffalo_l模型... {progress-35}/20", progress)

            # 启动进度模拟线程
            progress_thread = threading.Thread(target=simulate_progress)
            progress_thread.daemon = True
            progress_thread.start()

            try:
                app = insightface.app.FaceAnalysis(name='buffalo_l')
                app.prepare(ctx_id=-1, det_size=(640, 640))
                download_complete.set()  # 标记下载完成
                logger.info("✅ buffalo_l模型包下载完成")
            except Exception as e:
                download_complete.set()
                logger.error(f"buffalo_l下载失败: {e}")
                return False

            if progress_callback:
                progress_callback("buffalo_l模型下载完成", 60)

            # 下载inswapper模型 (如果还没有)
            inswapper_path = self.models_dir / "inswapper_128.onnx"
            if not inswapper_path.exists():
                if progress_callback:
                    progress_callback("正在下载inswapper模型...", 65)

                logger.info("正在下载inswapper模型...")
                try:
                    swapper = get_model('inswapper_128.onnx', download=True, download_zip=True)
                    logger.info("✅ inswapper模型下载完成")
                except Exception as e:
                    logger.warning(f"InsightFace inswapper下载失败: {e}")
                    # 尝试从Civitai下载
                    if not self._download_inswapper_from_civitai(progress_callback):
                        return False

            if progress_callback:
                progress_callback("正在复制模型文件...", 80)

            # 3. 复制模型到项目
            return self._copy_insightface_models()

        except Exception as e:
            logger.error(f"❌ InsightFace下载失败: {e}")
            return False

    def _copy_insightface_models(self) -> bool:
        """从InsightFace目录复制模型到项目"""
        logger.info("📋 复制InsightFace模型到项目...")

        insightface_root = Path.home() / '.insightface'

        # 文件映射 - 根据实际InsightFace buffalo_l模型包内容
        file_mapping = {
            'scrfd_10g_bnkps.onnx': ['det_10g.onnx'],
            'arcface_r100.onnx': ['w600k_r50.onnx'],  # buffalo_l中的识别模型
            'inswapper_128.onnx': ['inswapper_128.onnx']
        }

        success_count = 0

        for target_name, source_names in file_mapping.items():
            target_path = self.models_dir / target_name

            if target_path.exists():
                logger.info(f"✅ {target_name} 已存在")
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
                            logger.info(f"✅ 复制 {source_name} -> {target_name}")
                            success_count += 1
                            found = True
                            break
                        except Exception as e:
                            logger.error(f"❌ 复制失败: {e}")
                if found:
                    break

            if not found:
                logger.warning(f"⚠️ 未找到 {target_name}")

        return success_count >= 2  # 至少需要2个核心模型

    def download_models(self, progress_callback: Optional[Callable] = None) -> bool:
        """下载所有模型文件"""
        try:
            if progress_callback:
                progress_callback("开始下载模型文件...", 0)

            # 1. 先尝试下载InSwapper (最容易成功的)
            if not self._download_inswapper_from_civitai(progress_callback):
                logger.warning("⚠️ InSwapper下载失败，但继续尝试其他模型...")

            # 2. 设置InsightFace并下载其他模型
            if not self._setup_insightface_models(progress_callback):
                logger.error("❌ InsightFace模型下载失败")
                return False

            if progress_callback:
                progress_callback("模型下载完成！", 100)

            return True

        except Exception as e:
            logger.error(f"下载过程中出错: {e}")
            return False
    
    def download_ffmpeg(self, progress_callback: Optional[Callable] = None) -> bool:
        """下载FFmpeg工具"""
        system = platform.system().lower()
        if system == "windows":
            system_key = "windows"
        else:
            logger.error(f"暂不支持的操作系统: {system}")
            return False
        
        ffmpeg_config = self.config.get('ffmpeg', {}).get(system_key, {})
        if not ffmpeg_config:
            logger.error(f"没有找到 {system} 的FFmpeg配置")
            return False
        
        # 检查是否已安装
        required_files = ffmpeg_config.get('extract_files', ['ffmpeg.exe', 'ffplay.exe', 'ffprobe.exe'])
        all_exist = all((self.ffmpeg_dir / f).exists() for f in required_files)
        if all_exist:
            logger.info("FFmpeg已安装")
            if progress_callback:
                progress_callback("FFmpeg已安装", 100)
            return True
        
        # 下载FFmpeg
        if progress_callback:
            progress_callback("正在下载FFmpeg...", 0)
        
        url = ffmpeg_config['url']
        archive_name = Path(url).name
        archive_path = self.ffmpeg_dir / archive_name
        
        if not self._download_file(url, archive_path, progress_callback):
            return False
        
        # 解压
        if progress_callback:
            progress_callback("正在解压FFmpeg...", 80)
        
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                extract_files = ffmpeg_config.get('extract_files', [])
                for file_name in extract_files:
                    # 查找文件（可能在子目录中）
                    for zip_info in zip_ref.infolist():
                        if zip_info.filename.endswith(file_name):
                            # 提取到目标目录
                            with zip_ref.open(zip_info) as source:
                                target_path = self.ffmpeg_dir / file_name
                                with open(target_path, 'wb') as target:
                                    target.write(source.read())
                            break
        except Exception as e:
            logger.error(f"解压失败: {e}")
            return False
        
        # 清理压缩包
        archive_path.unlink()
        
        if progress_callback:
            progress_callback("FFmpeg安装完成", 100)
        
        return True
    
    def check_requirements(self) -> Dict[str, bool]:
        """检查所需文件是否存在"""
        status = {
            'models': {},
            'ffmpeg': {}
        }

        # 检查模型文件
        required_models = [
            "inswapper_128.onnx",      # 换脸生成模型
            "scrfd_10g_bnkps.onnx",    # 人脸检测模型
            "arcface_r100.onnx"        # 人脸识别模型
        ]

        for model_name in required_models:
            model_path = self.models_dir / model_name
            status['models'][model_name] = model_path.exists()

        # 检查FFmpeg
        required_files = ['ffmpeg.exe', 'ffplay.exe', 'ffprobe.exe']
        for file_name in required_files:
            file_path = self.ffmpeg_dir / file_name
            status['ffmpeg'][file_name] = file_path.exists()

        return status
    
    def download_all(self, progress_callback: Optional[Callable] = None) -> bool:
        """下载所有必需文件"""
        try:
            # 下载模型
            if progress_callback:
                progress_callback("开始下载模型文件...", 0)
            
            if not self.download_models(progress_callback):
                return False
            
            # 下载FFmpeg
            if progress_callback:
                progress_callback("开始下载FFmpeg...", 50)
            
            if not self.download_ffmpeg(progress_callback):
                return False
            
            if progress_callback:
                progress_callback("所有文件下载完成！", 100)
            
            return True
            
        except Exception as e:
            logger.error(f"下载过程中出错: {e}")
            return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    downloader = AutoDownloader()
    
    def progress_callback(message, progress):
        print(f"[{progress:.1f}%] {message}")
    
    print("检查必需文件...")
    status = downloader.check_requirements()
    
    missing_files = []
    for category, files in status.items():
        for filename, exists in files.items():
            if not exists:
                missing_files.append(f"{category}/{filename}")
    
    if missing_files:
        print(f"缺少文件: {missing_files}")
        print("开始下载...")
        success = downloader.download_all(progress_callback)
        if success:
            print("✅ 所有文件下载完成！")
        else:
            print("❌ 下载失败")
    else:
        print("✅ 所有必需文件已存在")
