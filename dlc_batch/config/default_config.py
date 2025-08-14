"""
默认配置文件

包含所有模块的默认参数配置。
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 默认配置
DEFAULT_CONFIG = {
    # 模型配置
    "models": {
        "inswapper": str(PROJECT_ROOT / "models" / "inswapper_128.onnx"),
        "detector": str(PROJECT_ROOT / "models" / "scrfd_10g_bnkps.onnx"),
        "recognizer": str(PROJECT_ROOT / "models" / "arcface_r100.onnx"),
        "segmentation": str(PROJECT_ROOT / "models" / "bisenet_face.onnx"),
        "enhancer": str(PROJECT_ROOT / "models" / "GFPGANv1.4.pth"),
    },
    
    # 检测参数
    "detection": {
        "det_size": [640, 640],
        "conf_threshold": 0.5,
        "nms_threshold": 0.4,
        "min_face_size": 64,
        "max_faces": 10,
    },
    
    # 识别参数
    "recognition": {
        "similarity_threshold": 0.6,
        "embedding_size": 512,
    },
    
    # 换脸参数
    "swapping": {
        "blend_ratio": 0.8,
        "use_segmentation": False,
        "color_correction": True,
        "enhance_face": False,
    },
    
    # 跟踪参数
    "tracking": {
        "max_disappeared": 30,
        "max_distance": 50,
        "track_buffer": 30,
    },
    
    # 处理参数
    "processing": {
        "batch_size": 1,
        "num_threads": 4,
        "memory_limit": "8GB",
    },
    
    # 性能参数
    "performance": {
        "providers": ["CUDAExecutionProvider", "CPUExecutionProvider"],
        "device_id": 0,
        "inter_op_num_threads": 0,
        "intra_op_num_threads": 0,
    },
    
    # 输出参数
    "output": {
        "fps": 30,
        "codec": "h264",
        "bitrate": "5000k",
        "audio_codec": "aac",
        "preserve_audio": True,
    },
    
    # 日志参数
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": None,  # None表示不写入文件
        "max_size": "10MB",
        "backup_count": 5,
    },
    
    # 路径配置
    "paths": {
        "models_dir": str(PROJECT_ROOT / "models"),
        "assets_dir": str(PROJECT_ROOT / "assets"),
        "input_dir": str(PROJECT_ROOT / "videos_in"),
        "output_dir": str(PROJECT_ROOT / "outputs"),
        "temp_dir": str(PROJECT_ROOT / "temp"),
        "cache_dir": str(PROJECT_ROOT / "cache"),
    },
}

# 质量预设配置
QUALITY_PRESETS = {
    "fast": {
        "detection": {"det_size": [320, 320]},
        "swapping": {"blend_ratio": 0.6, "use_segmentation": False, "enhance_face": False},
        "processing": {"batch_size": 4},
    },
    "balanced": {
        "detection": {"det_size": [480, 480]},
        "swapping": {"blend_ratio": 0.8, "use_segmentation": False, "enhance_face": False},
        "processing": {"batch_size": 2},
    },
    "high": {
        "detection": {"det_size": [640, 640]},
        "swapping": {"blend_ratio": 0.9, "use_segmentation": True, "enhance_face": True},
        "processing": {"batch_size": 1},
    },
}

# 环境变量映射
ENV_VAR_MAPPING = {
    "DLC_MODEL_PATH": "paths.models_dir",
    "DLC_OUTPUT_PATH": "paths.output_dir", 
    "DLC_LOG_LEVEL": "logging.level",
    "DLC_PROVIDERS": "performance.providers",
    "DLC_DEVICE_ID": "performance.device_id",
    "CUDA_VISIBLE_DEVICES": "performance.device_id",
}

def get_default_config():
    """获取默认配置"""
    return DEFAULT_CONFIG.copy()

def get_quality_preset(quality: str):
    """获取质量预设配置"""
    return QUALITY_PRESETS.get(quality, QUALITY_PRESETS["balanced"])

def apply_env_vars(config: dict):
    """应用环境变量到配置"""
    for env_var, config_path in ENV_VAR_MAPPING.items():
        value = os.getenv(env_var)
        if value is not None:
            keys = config_path.split(".")
            current = config
            for key in keys[:-1]:
                current = current.setdefault(key, {})
            
            # 类型转换
            if env_var in ["DLC_DEVICE_ID"]:
                value = int(value)
            elif env_var == "DLC_PROVIDERS":
                value = value.split(",")
            
            current[keys[-1]] = value
    
    return config
