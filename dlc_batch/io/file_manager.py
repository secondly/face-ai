"""
文件管理模块

提供文件和目录管理功能。
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Iterator, Tuple
from ..utils.logger import LoggerMixin
from ..utils.validators import get_video_files, validate_directory

class FileManager(LoggerMixin):
    """文件管理器"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化文件管理器
        
        Args:
            base_dir: 基础工作目录
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.logger.info(f"文件管理器初始化: {self.base_dir}")
    
    def ensure_directory(self, dir_path: str, create: bool = True) -> bool:
        """
        确保目录存在
        
        Args:
            dir_path: 目录路径
            create: 如果不存在是否创建
            
        Returns:
            bool: 目录是否存在或创建成功
        """
        return validate_directory(dir_path, create_if_missing=create)
    
    def get_safe_filename(self, filename: str, max_length: int = 255) -> str:
        """
        获取安全的文件名 (移除非法字符)
        
        Args:
            filename: 原始文件名
            max_length: 最大长度
            
        Returns:
            str: 安全的文件名
        """
        # 移除或替换非法字符
        illegal_chars = '<>:"/\\|?*'
        safe_name = filename
        
        for char in illegal_chars:
            safe_name = safe_name.replace(char, '_')
        
        # 限制长度
        if len(safe_name) > max_length:
            name, ext = os.path.splitext(safe_name)
            max_name_length = max_length - len(ext)
            safe_name = name[:max_name_length] + ext
        
        return safe_name
    
    def get_unique_filename(self, file_path: str) -> str:
        """
        获取唯一的文件名 (如果文件已存在，添加数字后缀)
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 唯一的文件路径
        """
        path = Path(file_path)
        
        if not path.exists():
            return str(path)
        
        # 分离文件名和扩展名
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        
        counter = 1
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            
            if not new_path.exists():
                return str(new_path)
            
            counter += 1
    
    def copy_file(self, src: str, dst: str, overwrite: bool = False) -> bool:
        """
        复制文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            overwrite: 是否覆盖已存在的文件
            
        Returns:
            bool: 是否成功
        """
        try:
            src_path = Path(src)
            dst_path = Path(dst)
            
            if not src_path.exists():
                self.logger.error(f"源文件不存在: {src}")
                return False
            
            if dst_path.exists() and not overwrite:
                self.logger.warning(f"目标文件已存在: {dst}")
                return False
            
            # 确保目标目录存在
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src, dst)
            self.logger.debug(f"文件复制成功: {src} -> {dst}")
            return True
            
        except Exception as e:
            self.logger.error(f"文件复制失败: {e}")
            return False
    
    def move_file(self, src: str, dst: str, overwrite: bool = False) -> bool:
        """
        移动文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            overwrite: 是否覆盖已存在的文件
            
        Returns:
            bool: 是否成功
        """
        try:
            src_path = Path(src)
            dst_path = Path(dst)
            
            if not src_path.exists():
                self.logger.error(f"源文件不存在: {src}")
                return False
            
            if dst_path.exists() and not overwrite:
                self.logger.warning(f"目标文件已存在: {dst}")
                return False
            
            # 确保目标目录存在
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(src, dst)
            self.logger.debug(f"文件移动成功: {src} -> {dst}")
            return True
            
        except Exception as e:
            self.logger.error(f"文件移动失败: {e}")
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                self.logger.debug(f"文件删除成功: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"文件删除失败: {e}")
            return False
    
    def get_file_size(self, file_path: str) -> int:
        """
        获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            int: 文件大小 (字节)，文件不存在返回-1
        """
        try:
            return Path(file_path).stat().st_size
        except Exception:
            return -1
    
    def get_file_hash(self, file_path: str, algorithm: str = 'sha256') -> Optional[str]:
        """
        计算文件哈希值
        
        Args:
            file_path: 文件路径
            algorithm: 哈希算法 ('md5', 'sha1', 'sha256')
            
        Returns:
            Optional[str]: 哈希值，失败返回None
        """
        try:
            hash_obj = hashlib.new(algorithm)
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            self.logger.error(f"计算文件哈希失败: {e}")
            return None

class BatchFileProcessor(LoggerMixin):
    """批量文件处理器"""
    
    def __init__(self, input_dir: str, output_dir: str, 
                 file_extensions: Optional[List[str]] = None):
        """
        初始化批量文件处理器
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            file_extensions: 支持的文件扩展名列表
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.file_extensions = file_extensions or ['.mp4', '.avi', '.mov', '.mkv']
        self.file_manager = FileManager()
        
        # 确保目录存在
        if not self.input_dir.exists():
            raise ValueError(f"输入目录不存在: {input_dir}")
        
        self.file_manager.ensure_directory(output_dir, create=True)
        
        self.logger.info(f"批量处理器初始化: {input_dir} -> {output_dir}")
    
    def get_input_files(self) -> List[Path]:
        """
        获取输入文件列表
        
        Returns:
            List[Path]: 输入文件路径列表
        """
        if self.file_extensions == ['.mp4', '.avi', '.mov', '.mkv']:
            # 使用专门的视频文件获取函数
            return get_video_files(self.input_dir, self.file_extensions)
        else:
            # 通用文件获取
            files = []
            for ext in self.file_extensions:
                files.extend(self.input_dir.glob(f"*{ext}"))
                files.extend(self.input_dir.glob(f"*{ext.upper()}"))
            return sorted(files)
    
    def get_output_path(self, input_file: Path, suffix: str = '') -> Path:
        """
        获取输出文件路径
        
        Args:
            input_file: 输入文件路径
            suffix: 文件名后缀
            
        Returns:
            Path: 输出文件路径
        """
        stem = input_file.stem + suffix
        output_file = self.output_dir / f"{stem}{input_file.suffix}"
        return output_file
    
    def process_files(self, processor_func, progress_callback=None, 
                     skip_existing: bool = True) -> Dict[str, bool]:
        """
        批量处理文件
        
        Args:
            processor_func: 处理函数 (input_path, output_path) -> bool
            progress_callback: 进度回调 (current, total, filename) -> None
            skip_existing: 是否跳过已存在的输出文件
            
        Returns:
            Dict[str, bool]: 文件路径到处理结果的映射
        """
        input_files = self.get_input_files()
        results = {}
        
        self.logger.info(f"开始批量处理 {len(input_files)} 个文件")
        
        for i, input_file in enumerate(input_files):
            output_file = self.get_output_path(input_file)
            
            # 检查是否跳过已存在的文件
            if skip_existing and output_file.exists():
                self.logger.info(f"跳过已存在的文件: {output_file}")
                results[str(input_file)] = True
                
                if progress_callback:
                    progress_callback(i + 1, len(input_files), input_file.name)
                continue
            
            # 处理文件
            try:
                success = processor_func(str(input_file), str(output_file))
                results[str(input_file)] = success
                
                if success:
                    self.logger.info(f"处理成功: {input_file.name}")
                else:
                    self.logger.error(f"处理失败: {input_file.name}")
                    
            except Exception as e:
                self.logger.error(f"处理异常: {input_file.name} - {e}")
                results[str(input_file)] = False
            
            # 进度回调
            if progress_callback:
                progress_callback(i + 1, len(input_files), input_file.name)
        
        # 统计结果
        success_count = sum(results.values())
        total_count = len(results)
        self.logger.info(f"批量处理完成: {success_count}/{total_count} 成功")
        
        return results
    
    def get_processing_summary(self, results: Dict[str, bool]) -> Dict[str, any]:
        """
        获取处理结果摘要
        
        Args:
            results: 处理结果字典
            
        Returns:
            Dict[str, any]: 摘要信息
        """
        total = len(results)
        success = sum(results.values())
        failed = total - success
        
        return {
            'total_files': total,
            'success_count': success,
            'failed_count': failed,
            'success_rate': success / total if total > 0 else 0,
            'failed_files': [path for path, success in results.items() if not success]
        }
