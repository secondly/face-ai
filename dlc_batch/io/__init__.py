"""
输入输出模块

负责视频读写、音频处理、文件管理等IO操作。
"""

from .video_reader import VideoReader, BatchVideoReader
from .video_writer import VideoWriter, VideoProcessor, create_video_from_frames, extract_frames_to_images
from .audio_processor import AudioProcessor, VideoAudioManager
from .file_manager import FileManager, BatchFileProcessor

__all__ = [
    'VideoReader',
    'BatchVideoReader',
    'VideoWriter',
    'VideoProcessor',
    'create_video_from_frames',
    'extract_frames_to_images',
    'AudioProcessor',
    'VideoAudioManager',
    'FileManager',
    'BatchFileProcessor'
]
