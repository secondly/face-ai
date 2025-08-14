"""
验证工具模块

提供文件、图像、视频等验证功能。
"""

import os
from pathlib import Path
from typing import Union, List, Optional

def validate_file(file_path: Union[str, Path], 
                 extensions: Optional[List[str]] = None,
                 check_readable: bool = True) -> bool:
    """
    验证文件是否存在且可访问
    
    Args:
        file_path: 文件路径
        extensions: 允许的文件扩展名列表 (如 ['.jpg', '.png'])
        check_readable: 是否检查文件可读性
    
    Returns:
        bool: 验证是否通过
    """
    path = Path(file_path)
    
    # 检查文件是否存在
    if not path.exists():
        return False
    
    # 检查是否为文件
    if not path.is_file():
        return False
    
    # 检查扩展名
    if extensions:
        if path.suffix.lower() not in [ext.lower() for ext in extensions]:
            return False
    
    # 检查可读性
    if check_readable:
        try:
            with open(path, 'rb') as f:
                f.read(1)  # 尝试读取1字节
        except (PermissionError, OSError):
            return False
    
    return True

def validate_image(image_path: Union[str, Path]) -> bool:
    """
    验证图像文件
    
    Args:
        image_path: 图像文件路径
    
    Returns:
        bool: 验证是否通过
    """
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
    
    if not validate_file(image_path, image_extensions):
        return False
    
    # 尝试用OpenCV读取图像
    try:
        import cv2
        img = cv2.imread(str(image_path))
        return img is not None
    except ImportError:
        # 如果OpenCV不可用，只检查文件扩展名
        return True

def validate_video(video_path: Union[str, Path]) -> bool:
    """
    验证视频文件
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        bool: 验证是否通过
    """
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm']
    
    if not validate_file(video_path, video_extensions):
        return False
    
    # 尝试用OpenCV读取视频
    try:
        import cv2
        cap = cv2.VideoCapture(str(video_path))
        ret = cap.isOpened()
        cap.release()
        return ret
    except ImportError:
        # 如果OpenCV不可用，只检查文件扩展名
        return True

def validate_directory(dir_path: Union[str, Path], 
                      create_if_missing: bool = False) -> bool:
    """
    验证目录是否存在且可访问
    
    Args:
        dir_path: 目录路径
        create_if_missing: 如果目录不存在是否创建
    
    Returns:
        bool: 验证是否通过
    """
    path = Path(dir_path)
    
    if not path.exists():
        if create_if_missing:
            try:
                path.mkdir(parents=True, exist_ok=True)
                return True
            except (PermissionError, OSError):
                return False
        else:
            return False
    
    return path.is_dir()

def validate_model_file(model_path: Union[str, Path]) -> bool:
    """
    验证ONNX模型文件
    
    Args:
        model_path: 模型文件路径
    
    Returns:
        bool: 验证是否通过
    """
    if not validate_file(model_path, ['.onnx']):
        return False
    
    # 尝试加载ONNX模型
    try:
        import onnxruntime as ort
        session = ort.InferenceSession(str(model_path), providers=['CPUExecutionProvider'])
        return True
    except Exception:
        return False

def validate_config(config: dict, required_keys: List[str]) -> bool:
    """
    验证配置字典
    
    Args:
        config: 配置字典
        required_keys: 必需的键列表
    
    Returns:
        bool: 验证是否通过
    """
    for key in required_keys:
        if key not in config:
            return False
        
        # 检查嵌套键 (如 'models.detector')
        if '.' in key:
            keys = key.split('.')
            current = config
            for k in keys:
                if k not in current:
                    return False
                current = current[k]
    
    return True

def get_video_files(directory: Union[str, Path], 
                   extensions: Optional[List[str]] = None) -> List[Path]:
    """
    获取目录下的所有视频文件
    
    Args:
        directory: 目录路径
        extensions: 视频文件扩展名列表
    
    Returns:
        List[Path]: 视频文件路径列表
    """
    if extensions is None:
        extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm']
    
    directory = Path(directory)
    if not directory.is_dir():
        return []
    
    video_files = []
    for ext in extensions:
        video_files.extend(directory.glob(f"*{ext}"))
        video_files.extend(directory.glob(f"*{ext.upper()}"))
    
    return sorted(video_files)

def validate_providers(providers: List[str]) -> List[str]:
    """
    验证并过滤可用的ONNX Runtime提供者
    
    Args:
        providers: 提供者列表
    
    Returns:
        List[str]: 可用的提供者列表
    """
    try:
        import onnxruntime as ort
        available_providers = ort.get_available_providers()
        
        # 提供者名称映射
        provider_mapping = {
            'cuda': 'CUDAExecutionProvider',
            'cpu': 'CPUExecutionProvider',
            'tensorrt': 'TensorrtExecutionProvider',
            'openvino': 'OpenVINOExecutionProvider',
            'dml': 'DmlExecutionProvider',  # DirectML (Windows)
        }
        
        valid_providers = []
        for provider in providers:
            if provider in provider_mapping:
                mapped_provider = provider_mapping[provider]
                if mapped_provider in available_providers:
                    valid_providers.append(mapped_provider)
            elif provider in available_providers:
                valid_providers.append(provider)
        
        # 确保至少有CPU提供者
        if not valid_providers and 'CPUExecutionProvider' in available_providers:
            valid_providers.append('CPUExecutionProvider')
        
        return valid_providers
        
    except ImportError:
        return ['CPUExecutionProvider']
