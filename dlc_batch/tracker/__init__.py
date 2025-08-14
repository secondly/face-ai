"""
人脸跟踪模块

负责跨帧人脸跟踪、身份管理和一致性维护。
"""

from .face_tracker import FaceTracker
from .identity_manager import IdentityManager

__all__ = [
    'FaceTracker',
    'IdentityManager'
]
