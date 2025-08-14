"""
自动下载器 - 下载必要的模型文件和工具
"""

import os
import json
import hashlib
import zipfile
import requests
import platform
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
                            progress_callback(progress, downloaded, total_size)
            
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
    
    def download_models(self, progress_callback: Optional[Callable] = None) -> bool:
        """下载所有模型文件"""
        models_config = self.config.get('models', {})
        total_models = len(models_config)
        
        for i, (model_name, model_info) in enumerate(models_config.items()):
            model_path = self.models_dir / model_name
            
            # 检查文件是否已存在且有效
            if self._verify_file(model_path, model_info.get('md5')):
                logger.info(f"模型已存在: {model_name}")
                if progress_callback:
                    progress_callback(f"模型 {model_name} 已存在", (i + 1) / total_models * 100)
                continue
            
            # 尝试下载
            urls = [model_info['url']] + model_info.get('backup_urls', [])
            success = False
            
            for url in urls:
                if progress_callback:
                    progress_callback(f"正在下载 {model_name}...", i / total_models * 100)
                
                if self._download_file(url, model_path, progress_callback):
                    if self._verify_file(model_path, model_info.get('md5')):
                        success = True
                        break
                    else:
                        logger.warning(f"文件验证失败，尝试下一个URL: {model_name}")
            
            if not success:
                logger.error(f"模型下载失败: {model_name}")
                return False
        
        return True
    
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
        models_config = self.config.get('models', {})
        for model_name in models_config.keys():
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
