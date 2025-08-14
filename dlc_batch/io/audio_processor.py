"""
音频处理模块

提供音频提取、合并和处理功能。
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from ..utils.logger import LoggerMixin

class AudioProcessor(LoggerMixin):
    """音频处理器"""
    
    def __init__(self, ffmpeg_path: str = 'ffmpeg'):
        """
        初始化音频处理器
        
        Args:
            ffmpeg_path: FFmpeg可执行文件路径
        """
        self.ffmpeg_path = ffmpeg_path
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """检查FFmpeg是否可用"""
        try:
            result = subprocess.run([self.ffmpeg_path, '-version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError("FFmpeg不可用")
        except FileNotFoundError:
            raise RuntimeError(f"找不到FFmpeg: {self.ffmpeg_path}")
    
    def _run_ffmpeg(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """
        运行FFmpeg命令
        
        Args:
            args: FFmpeg参数列表
            check: 是否检查返回码
            
        Returns:
            subprocess.CompletedProcess: 执行结果
        """
        cmd = [self.ffmpeg_path] + args
        self.logger.debug(f"执行FFmpeg命令: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if check and result.returncode != 0:
            self.logger.error(f"FFmpeg命令失败: {result.stderr}")
            raise RuntimeError(f"FFmpeg执行失败: {result.stderr}")
        
        return result
    
    def extract_audio(self, video_path: str, audio_path: str, 
                     audio_codec: str = 'aac', audio_bitrate: str = '128k') -> bool:
        """
        从视频中提取音频
        
        Args:
            video_path: 输入视频路径
            audio_path: 输出音频路径
            audio_codec: 音频编码器
            audio_bitrate: 音频比特率
            
        Returns:
            bool: 是否成功
        """
        try:
            args = [
                '-i', str(video_path),
                '-vn',  # 不包含视频
                '-acodec', audio_codec,
                '-ab', audio_bitrate,
                '-y',  # 覆盖输出文件
                str(audio_path)
            ]
            
            self._run_ffmpeg(args)
            self.logger.info(f"音频提取成功: {audio_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"音频提取失败: {e}")
            return False
    
    def merge_video_audio(self, video_path: str, audio_path: str, 
                         output_path: str, video_codec: str = 'copy',
                         audio_codec: str = 'aac') -> bool:
        """
        合并视频和音频
        
        Args:
            video_path: 输入视频路径
            audio_path: 输入音频路径
            output_path: 输出视频路径
            video_codec: 视频编码器 ('copy' 表示不重编码)
            audio_codec: 音频编码器
            
        Returns:
            bool: 是否成功
        """
        try:
            args = [
                '-i', str(video_path),
                '-i', str(audio_path),
                '-c:v', video_codec,
                '-c:a', audio_codec,
                '-map', '0:v:0',  # 使用第一个输入的视频流
                '-map', '1:a:0',  # 使用第二个输入的音频流
                '-shortest',      # 以最短流为准
                '-y',             # 覆盖输出文件
                str(output_path)
            ]
            
            self._run_ffmpeg(args)
            self.logger.info(f"视频音频合并成功: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"视频音频合并失败: {e}")
            return False
    
    def copy_audio_track(self, source_video: str, target_video: str, 
                        output_path: str) -> bool:
        """
        从源视频复制音轨到目标视频
        
        Args:
            source_video: 源视频路径 (提供音轨)
            target_video: 目标视频路径 (提供视频)
            output_path: 输出视频路径
            
        Returns:
            bool: 是否成功
        """
        try:
            args = [
                '-i', str(target_video),  # 视频源
                '-i', str(source_video),  # 音频源
                '-c:v', 'copy',           # 复制视频流
                '-c:a', 'aac',            # 重编码音频
                '-map', '0:v:0',          # 使用第一个输入的视频
                '-map', '1:a:0',          # 使用第二个输入的音频
                '-shortest',              # 以最短流为准
                '-y',                     # 覆盖输出文件
                str(output_path)
            ]
            
            self._run_ffmpeg(args)
            self.logger.info(f"音轨复制成功: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"音轨复制失败: {e}")
            return False
    
    def has_audio(self, video_path: str) -> bool:
        """
        检查视频是否包含音频流
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            bool: 是否包含音频
        """
        try:
            args = [
                '-i', str(video_path),
                '-hide_banner',
                '-f', 'null', '-'
            ]
            
            result = self._run_ffmpeg(args, check=False)
            
            # 检查stderr中是否包含音频流信息
            return 'Audio:' in result.stderr
            
        except Exception:
            return False
    
    def get_audio_info(self, video_path: str) -> Optional[Dict[str, Any]]:
        """
        获取视频的音频信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 音频信息，无音频返回None
        """
        try:
            args = [
                '-i', str(video_path),
                '-hide_banner'
            ]
            
            result = self._run_ffmpeg(args, check=False)
            
            # 解析音频信息
            audio_info = {}
            lines = result.stderr.split('\n')
            
            for line in lines:
                if 'Audio:' in line:
                    # 解析音频流信息
                    parts = line.strip().split(',')
                    if len(parts) >= 3:
                        audio_info['codec'] = parts[0].split('Audio:')[1].strip()
                        audio_info['sample_rate'] = parts[1].strip()
                        audio_info['channels'] = parts[2].strip()
                    break
            
            return audio_info if audio_info else None
            
        except Exception:
            return None
    
    def remove_audio(self, video_path: str, output_path: str) -> bool:
        """
        移除视频中的音频流
        
        Args:
            video_path: 输入视频路径
            output_path: 输出视频路径
            
        Returns:
            bool: 是否成功
        """
        try:
            args = [
                '-i', str(video_path),
                '-c:v', 'copy',  # 复制视频流
                '-an',           # 移除音频流
                '-y',            # 覆盖输出文件
                str(output_path)
            ]
            
            self._run_ffmpeg(args)
            self.logger.info(f"音频移除成功: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"音频移除失败: {e}")
            return False

class VideoAudioManager:
    """视频音频管理器 - 处理换脸过程中的音频保留"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        初始化视频音频管理器
        
        Args:
            temp_dir: 临时文件目录
        """
        self.audio_processor = AudioProcessor()
        self.temp_dir = Path(temp_dir) if temp_dir else None
        self.temp_files = []
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口 - 清理临时文件"""
        self.cleanup()
    
    def process_video_with_audio_preservation(self, input_video: str, 
                                            processed_video: str, 
                                            output_video: str) -> bool:
        """
        处理视频并保留原音轨
        
        Args:
            input_video: 原始视频路径
            processed_video: 处理后的视频路径 (无音频)
            output_video: 最终输出视频路径
            
        Returns:
            bool: 是否成功
        """
        # 检查原视频是否有音频
        if not self.audio_processor.has_audio(input_video):
            # 没有音频，直接复制处理后的视频
            import shutil
            shutil.copy2(processed_video, output_video)
            return True
        
        # 有音频，需要复制音轨
        return self.audio_processor.copy_audio_track(
            source_video=input_video,
            target_video=processed_video,
            output_path=output_video
        )
    
    def create_temp_file(self, suffix: str = '.tmp') -> str:
        """
        创建临时文件
        
        Args:
            suffix: 文件后缀
            
        Returns:
            str: 临时文件路径
        """
        if self.temp_dir:
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            temp_file = tempfile.NamedTemporaryFile(
                suffix=suffix, dir=self.temp_dir, delete=False
            )
        else:
            temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        
        temp_path = temp_file.name
        temp_file.close()
        
        self.temp_files.append(temp_path)
        return temp_path
    
    def cleanup(self):
        """清理临时文件"""
        for temp_file in self.temp_files:
            try:
                Path(temp_file).unlink(missing_ok=True)
            except Exception:
                pass
        self.temp_files.clear()
