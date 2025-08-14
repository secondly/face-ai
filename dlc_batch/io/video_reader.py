"""
视频读取模块

提供视频文件读取和帧处理功能。
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Iterator, Tuple, Optional, Dict, Any
from ..utils.logger import LoggerMixin
from ..utils.validators import validate_video

class VideoReader(LoggerMixin):
    """视频读取器"""
    
    def __init__(self, video_path: str, start_frame: int = 0, end_frame: Optional[int] = None):
        """
        初始化视频读取器
        
        Args:
            video_path: 视频文件路径
            start_frame: 开始帧号
            end_frame: 结束帧号，None表示读取到末尾
        """
        self.video_path = Path(video_path)
        self.start_frame = start_frame
        self.end_frame = end_frame
        self.cap = None
        self._info = None
        
        # 验证视频文件
        if not validate_video(self.video_path):
            raise ValueError(f"无效的视频文件: {self.video_path}")
        
        self.logger.info(f"初始化视频读取器: {self.video_path}")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
    
    def open(self):
        """打开视频文件"""
        if self.cap is not None:
            self.close()
        
        self.cap = cv2.VideoCapture(str(self.video_path))
        if not self.cap.isOpened():
            raise RuntimeError(f"无法打开视频文件: {self.video_path}")
        
        # 跳转到开始帧
        if self.start_frame > 0:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)
        
        self.logger.debug(f"视频文件已打开: {self.video_path}")
    
    def close(self):
        """关闭视频文件"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            self.logger.debug(f"视频文件已关闭: {self.video_path}")
    
    @property
    def info(self) -> Dict[str, Any]:
        """获取视频信息"""
        if self._info is None:
            if self.cap is None:
                self.open()
            
            self._info = {
                'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': self.cap.get(cv2.CAP_PROP_FPS),
                'frame_count': int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'duration': self.cap.get(cv2.CAP_PROP_FRAME_COUNT) / self.cap.get(cv2.CAP_PROP_FPS),
                'fourcc': int(self.cap.get(cv2.CAP_PROP_FOURCC)),
            }
            
            # 计算实际处理的帧数
            actual_end = self.end_frame if self.end_frame is not None else self._info['frame_count']
            self._info['actual_frame_count'] = max(0, actual_end - self.start_frame)
            
        return self._info
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        读取单帧
        
        Returns:
            Tuple[bool, Optional[np.ndarray]]: (是否成功, 帧数据)
        """
        if self.cap is None:
            self.open()
        
        # 检查是否超出结束帧
        if self.end_frame is not None:
            current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            if current_frame >= self.end_frame:
                return False, None
        
        ret, frame = self.cap.read()
        return ret, frame
    
    def read_frames(self) -> Iterator[Tuple[int, np.ndarray]]:
        """
        逐帧读取视频
        
        Yields:
            Tuple[int, np.ndarray]: (帧号, 帧数据)
        """
        if self.cap is None:
            self.open()
        
        frame_idx = self.start_frame
        
        while True:
            ret, frame = self.read_frame()
            if not ret:
                break
            
            yield frame_idx, frame
            frame_idx += 1
    
    def seek(self, frame_number: int) -> bool:
        """
        跳转到指定帧
        
        Args:
            frame_number: 目标帧号
            
        Returns:
            bool: 是否成功
        """
        if self.cap is None:
            self.open()
        
        # 检查帧号范围
        if frame_number < self.start_frame:
            frame_number = self.start_frame
        
        if self.end_frame is not None and frame_number >= self.end_frame:
            frame_number = self.end_frame - 1
        
        return self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    
    def get_current_frame_number(self) -> int:
        """获取当前帧号"""
        if self.cap is None:
            return self.start_frame
        return int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
    
    def get_frame_at(self, frame_number: int) -> Optional[np.ndarray]:
        """
        获取指定帧的数据
        
        Args:
            frame_number: 帧号
            
        Returns:
            Optional[np.ndarray]: 帧数据，失败返回None
        """
        current_pos = self.get_current_frame_number()
        
        if self.seek(frame_number):
            ret, frame = self.read_frame()
            # 恢复原位置
            self.seek(current_pos)
            return frame if ret else None
        
        return None
    
    def extract_frames(self, frame_numbers: list) -> Dict[int, np.ndarray]:
        """
        提取指定帧号的帧数据
        
        Args:
            frame_numbers: 帧号列表
            
        Returns:
            Dict[int, np.ndarray]: 帧号到帧数据的映射
        """
        frames = {}
        current_pos = self.get_current_frame_number()
        
        for frame_num in sorted(frame_numbers):
            frame = self.get_frame_at(frame_num)
            if frame is not None:
                frames[frame_num] = frame
        
        # 恢复原位置
        self.seek(current_pos)
        return frames
    
    def get_sample_frames(self, count: int = 10) -> Dict[int, np.ndarray]:
        """
        获取采样帧用于预览或分析
        
        Args:
            count: 采样帧数
            
        Returns:
            Dict[int, np.ndarray]: 帧号到帧数据的映射
        """
        info = self.info
        total_frames = info['actual_frame_count']
        
        if total_frames <= count:
            # 如果总帧数不多，返回所有帧
            frame_numbers = list(range(self.start_frame, 
                                     self.start_frame + total_frames))
        else:
            # 均匀采样
            step = total_frames // count
            frame_numbers = [self.start_frame + i * step for i in range(count)]
        
        return self.extract_frames(frame_numbers)
    
    def __len__(self) -> int:
        """返回视频帧数"""
        return self.info['actual_frame_count']
    
    def __repr__(self) -> str:
        """字符串表示"""
        info = self.info
        return (f"VideoReader(path='{self.video_path}', "
                f"frames={info['actual_frame_count']}, "
                f"fps={info['fps']:.2f}, "
                f"resolution={info['width']}x{info['height']})")

class BatchVideoReader:
    """批量视频读取器"""
    
    def __init__(self, video_paths: list, **kwargs):
        """
        初始化批量视频读取器
        
        Args:
            video_paths: 视频文件路径列表
            **kwargs: 传递给VideoReader的参数
        """
        self.video_paths = [Path(p) for p in video_paths]
        self.reader_kwargs = kwargs
        self.current_reader = None
        self.current_index = 0
    
    def __iter__(self):
        """迭代器接口"""
        self.current_index = 0
        return self
    
    def __next__(self):
        """获取下一个视频读取器"""
        if self.current_index >= len(self.video_paths):
            raise StopIteration
        
        video_path = self.video_paths[self.current_index]
        self.current_index += 1
        
        return VideoReader(video_path, **self.reader_kwargs)
    
    def __len__(self):
        """返回视频数量"""
        return len(self.video_paths)
