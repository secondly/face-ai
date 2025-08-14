"""
Deep-Live-Cam 实时换脸系统

基于ONNX的实时换脸系统，支持一键换脸、无需训练、可实时处理。

主要功能:
- 单视频换脸处理
- 批量视频处理
- 实时摄像头换脸
- 多人脸处理和跟踪
- 画质优化和增强

技术栈:
- ONNX Runtime (推理引擎)
- OpenCV (计算机视觉)
- InsightFace (人脸处理)
- FFmpeg (视频处理)
"""

__version__ = "1.0.0"
__author__ = "Deep-Live-Cam Team"
__email__ = "support@example.com"
__description__ = "基于ONNX的实时换脸系统"

# 导入核心模块
from . import engine
from . import tracker
from . import io
from . import config
from . import utils

# 版本信息
VERSION_INFO = {
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "python_requires": ">=3.9",
    "dependencies": [
        "onnxruntime-gpu>=1.15.0",
        "opencv-python>=4.8.0",
        "insightface>=0.7.3",
        "numpy>=1.21.0",
        "ffmpeg-python>=0.2.0",
        "tqdm>=4.64.0",
        "rich>=13.0.0",
        "pyyaml>=6.0",
    ]
}

def get_version():
    """获取版本信息"""
    return __version__

def get_info():
    """获取完整信息"""
    return VERSION_INFO
