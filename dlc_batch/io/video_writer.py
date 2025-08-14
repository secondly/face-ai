"""
视频写入模块

提供视频文件写入和编码功能。
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from ..utils.logger import LoggerMixin

class VideoWriter(LoggerMixin):
    """视频写入器"""
    
    def __init__(self, output_path: str, width: int, height: int, fps: float = 30.0,
                 codec: str = 'mp4v', bitrate: Optional[str] = None):
        """
        初始化视频写入器
        
        Args:
            output_path: 输出视频路径
            width: 视频宽度
            height: 视频高度
            fps: 帧率
            codec: 编码器 ('mp4v', 'h264', 'h265', 'xvid')
            bitrate: 比特率 (如 '5000k')
        """
        self.output_path = Path(output_path)
        self.width = width
        self.height = height
        self.fps = fps
        self.codec = codec
        self.bitrate = bitrate
        self.writer = None
        self.frame_count = 0
        
        # 创建输出目录
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"初始化视频写入器: {self.output_path} ({width}x{height}@{fps}fps)")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
    
    def _get_fourcc(self) -> int:
        """获取编码器FourCC"""
        codec_map = {
            'mp4v': cv2.VideoWriter_fourcc(*'mp4v'),
            'h264': cv2.VideoWriter_fourcc(*'H264'),
            'h265': cv2.VideoWriter_fourcc(*'H265'),
            'xvid': cv2.VideoWriter_fourcc(*'XVID'),
            'mjpg': cv2.VideoWriter_fourcc(*'MJPG'),
            'x264': cv2.VideoWriter_fourcc(*'X264'),
        }
        
        return codec_map.get(self.codec.lower(), cv2.VideoWriter_fourcc(*'mp4v'))
    
    def open(self):
        """打开视频写入器"""
        if self.writer is not None:
            self.close()
        
        fourcc = self._get_fourcc()
        self.writer = cv2.VideoWriter(
            str(self.output_path),
            fourcc,
            self.fps,
            (self.width, self.height)
        )
        
        if not self.writer.isOpened():
            raise RuntimeError(f"无法创建视频写入器: {self.output_path}")
        
        self.logger.debug(f"视频写入器已打开: {self.output_path}")
    
    def close(self):
        """关闭视频写入器"""
        if self.writer is not None:
            self.writer.release()
            self.writer = None
            self.logger.info(f"视频写入完成: {self.output_path} ({self.frame_count} 帧)")
    
    def write_frame(self, frame: np.ndarray) -> bool:
        """
        写入单帧
        
        Args:
            frame: 帧数据 (BGR格式)
            
        Returns:
            bool: 是否成功
        """
        if self.writer is None:
            self.open()
        
        # 检查帧尺寸
        if frame.shape[:2] != (self.height, self.width):
            frame = cv2.resize(frame, (self.width, self.height))
        
        # 确保是3通道BGR格式
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            self.writer.write(frame)
            self.frame_count += 1
            return True
        else:
            self.logger.warning(f"无效的帧格式: {frame.shape}")
            return False
    
    def write_frames(self, frames: list) -> int:
        """
        批量写入帧
        
        Args:
            frames: 帧数据列表
            
        Returns:
            int: 成功写入的帧数
        """
        success_count = 0
        for frame in frames:
            if self.write_frame(frame):
                success_count += 1
        
        return success_count
    
    @property
    def info(self) -> Dict[str, Any]:
        """获取写入器信息"""
        return {
            'output_path': str(self.output_path),
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'codec': self.codec,
            'frame_count': self.frame_count,
            'duration': self.frame_count / self.fps if self.fps > 0 else 0,
        }
    
    def __repr__(self) -> str:
        """字符串表示"""
        return (f"VideoWriter(path='{self.output_path}', "
                f"resolution={self.width}x{self.height}, "
                f"fps={self.fps}, codec='{self.codec}', "
                f"frames={self.frame_count})")

class VideoProcessor:
    """视频处理器 - 结合读取和写入"""
    
    def __init__(self, input_path: str, output_path: str, 
                 preserve_properties: bool = True, **writer_kwargs):
        """
        初始化视频处理器
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            preserve_properties: 是否保持原视频属性
            **writer_kwargs: 传递给VideoWriter的参数
        """
        from .video_reader import VideoReader
        
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.preserve_properties = preserve_properties
        self.writer_kwargs = writer_kwargs
        
        # 初始化读取器获取视频信息
        with VideoReader(input_path) as reader:
            self.input_info = reader.info
        
        # 设置写入器参数
        if preserve_properties:
            self.writer_kwargs.setdefault('width', self.input_info['width'])
            self.writer_kwargs.setdefault('height', self.input_info['height'])
            self.writer_kwargs.setdefault('fps', self.input_info['fps'])
    
    def process_frames(self, frame_processor, progress_callback=None):
        """
        处理视频帧
        
        Args:
            frame_processor: 帧处理函数 (frame) -> processed_frame
            progress_callback: 进度回调函数 (current, total) -> None
        """
        from .video_reader import VideoReader
        
        with VideoReader(self.input_path) as reader:
            with VideoWriter(self.output_path, **self.writer_kwargs) as writer:
                total_frames = len(reader)
                
                for frame_idx, frame in reader.read_frames():
                    # 处理帧
                    processed_frame = frame_processor(frame)
                    
                    # 写入处理后的帧
                    if processed_frame is not None:
                        writer.write_frame(processed_frame)
                    
                    # 进度回调
                    if progress_callback:
                        current = frame_idx - reader.start_frame + 1
                        progress_callback(current, total_frames)
    
    def copy_with_processing(self, frame_processor=None, progress_callback=None):
        """
        复制视频并可选地处理帧
        
        Args:
            frame_processor: 可选的帧处理函数
            progress_callback: 进度回调函数
        """
        if frame_processor is None:
            frame_processor = lambda x: x  # 直接复制
        
        self.process_frames(frame_processor, progress_callback)

def create_video_from_frames(frames: list, output_path: str, fps: float = 30.0,
                           codec: str = 'mp4v') -> bool:
    """
    从帧列表创建视频
    
    Args:
        frames: 帧数据列表
        output_path: 输出视频路径
        fps: 帧率
        codec: 编码器
        
    Returns:
        bool: 是否成功
    """
    if not frames:
        return False
    
    # 获取第一帧的尺寸
    first_frame = frames[0]
    height, width = first_frame.shape[:2]
    
    try:
        with VideoWriter(output_path, width, height, fps, codec) as writer:
            success_count = writer.write_frames(frames)
            return success_count == len(frames)
    except Exception as e:
        print(f"创建视频失败: {e}")
        return False

def extract_frames_to_images(video_path: str, output_dir: str, 
                           frame_numbers: Optional[list] = None,
                           image_format: str = 'jpg') -> Dict[int, str]:
    """
    提取视频帧为图像文件
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        frame_numbers: 指定帧号列表，None表示提取所有帧
        image_format: 图像格式 ('jpg', 'png')
        
    Returns:
        Dict[int, str]: 帧号到图像文件路径的映射
    """
    from .video_reader import VideoReader
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    saved_frames = {}
    
    with VideoReader(video_path) as reader:
        if frame_numbers is None:
            # 提取所有帧
            for frame_idx, frame in reader.read_frames():
                image_path = output_dir / f"frame_{frame_idx:06d}.{image_format}"
                if cv2.imwrite(str(image_path), frame):
                    saved_frames[frame_idx] = str(image_path)
        else:
            # 提取指定帧
            frames = reader.extract_frames(frame_numbers)
            for frame_idx, frame in frames.items():
                image_path = output_dir / f"frame_{frame_idx:06d}.{image_format}"
                if cv2.imwrite(str(image_path), frame):
                    saved_frames[frame_idx] = str(image_path)
    
    return saved_frames
