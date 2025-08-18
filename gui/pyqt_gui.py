#!/usr/bin/env python3
"""
PyQt5现代化GUI界面
提供专业级的用户界面体验
"""

import sys
import os
from pathlib import Path
import threading
import datetime
import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QProgressBar,
    QFileDialog, QMessageBox, QCheckBox, QFrame, QSplitter,
    QGroupBox, QGridLayout, QSpacerItem, QSizePolicy, QDialog,
    QComboBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.face_swapper import FaceSwapper

class ProcessWorker(QThread):
    """处理工作线程"""
    progress_updated = pyqtSignal(str, int)  # 状态文本, 进度百分比
    log_message = pyqtSignal(str, str)  # 消息, 级别
    finished = pyqtSignal(bool)  # 是否成功
    preview_updated = pyqtSignal(object, object, str)  # 原图, 结果图, 信息
    model_fallback_occurred = pyqtSignal(dict)  # 新增：模型回退信号

    def __init__(self, face_swapper, source_path, target_path, output_path, target_face_index=None, selected_face_indices=None, reference_frame_index=None,
                 background_enabled=False, background_mode="backgroundmattingv2", background_path=None, background_folder_path=None):
        super().__init__()
        self.face_swapper = face_swapper
        self.source_path = source_path
        self.target_path = target_path
        self.output_path = output_path
        self.target_face_index = target_face_index  # 目标人脸索引，None表示自动选择（旧版兼容）
        self.selected_face_indices = selected_face_indices  # 选中的人脸索引列表（新版多人脸选择）
        self.reference_frame_index = reference_frame_index  # 参考帧索引（新版多人脸选择）
        self.stop_requested = False

        # 背景替换相关参数
        self.background_enabled = background_enabled
        self.background_mode = background_mode
        self.background_path = background_path
        self.background_folder_path = background_folder_path
        self.background_replacer = None

        # 初始化背景替换器（延迟初始化，避免阻塞主线程）
        if self.background_enabled:
            try:
                from core.background_replacer import BackgroundReplacer
                # 使用延迟初始化，避免在主线程中下载模型
                self.background_replacer = BackgroundReplacer(mode=background_mode, lazy_init=True)
                self.log_message.emit(f"背景替换器创建成功，模式: {background_mode}", "INFO")
                self.log_message.emit("将在处理时初始化背景替换模型...", "INFO")
            except Exception as e:
                self.log_message.emit(f"背景替换模块加载失败: {e}", "ERROR")
                self.background_enabled = False
    
    def _get_mode_display_name(self, mode):
        """获取模式的显示名称"""
        mode_map = {
            'backgroundmattingv2': "BackgroundMattingV2 (推荐)",
            'modnet': "MODNet (快速)",
            'u2net': "U2Net (通用)",
            'rembg': "Rembg (简单)"
        }
        return mode_map.get(mode.lower(), mode)

    def stop(self):
        """停止处理"""
        self.stop_requested = True

    def _apply_background_replacement(self, image):
        """应用背景替换"""
        try:
            if not self.background_replacer:
                return image

            # 检查模型是否已初始化
            if not self.background_replacer.is_available():
                if self.background_replacer.is_initializing_model():
                    self.log_message.emit("背景替换模型正在初始化中，跳过此帧", "INFO")
                    return image

                # 初始化模型
                self.log_message.emit("正在初始化背景替换模型，请稍候...", "INFO")

                def progress_callback(current, total, message):
                    self.log_message.emit(f"模型初始化: {message} ({current}/{total})", "INFO")

                # 在当前线程中初始化（因为已经在worker线程中）
                self.background_replacer.initialize_async(progress_callback)

                # 检查初始化结果
                if not self.background_replacer.is_available():
                    error = self.background_replacer.get_initialization_error()
                    self.log_message.emit(f"背景替换模型初始化失败: {error}", "ERROR")
                    return image
                else:
                    # 检查是否发生了回退
                    status = self.background_replacer.get_model_status()
                    if status['fallback_occurred']:
                        original_display = self._get_mode_display_name(status['original_mode'])
                        current_display = self._get_mode_display_name(status['current_mode'])
                        self.log_message.emit(f"背景替换模型初始化成功，但从 {original_display} 回退到 {current_display} 模式", "WARNING")
                        if status.get('fallback_reason'):
                            self.log_message.emit(f"回退原因: {status['fallback_reason']}", "WARNING")
                        # 发送回退状态信号
                        self.model_fallback_occurred.emit(status)
                    else:
                        current_display = self._get_mode_display_name(status['current_mode'])
                        self.log_message.emit(f"背景替换模型初始化成功: {current_display}", "SUCCESS")

            # 获取背景图片
            background_image = self._get_background_image()
            if background_image is None:
                self.log_message.emit("无法获取背景图片，跳过背景替换", "WARNING")
                return image

            # 执行背景替换
            self.log_message.emit("正在进行背景替换...", "INFO")
            result = self.background_replacer.replace_background(image, background_image)

            if result is not None:
                self.log_message.emit("背景替换成功", "SUCCESS")
                return result
            else:
                self.log_message.emit("背景替换失败，使用原图", "WARNING")
                return image

        except Exception as e:
            self.log_message.emit(f"背景替换过程中出错: {e}", "ERROR")
            return image

    def _process_video_with_background(self):
        """处理视频（包含背景替换）"""
        import cv2
        from pathlib import Path

        try:
            self.log_message.emit("开始处理视频（包含背景替换）...", "INFO")

            # 确保背景替换器已初始化
            if not self.background_replacer.is_available():
                if self.background_replacer.is_initializing_model():
                    self.log_message.emit("背景替换模型正在初始化中，请稍候...", "INFO")
                    return False

                # 初始化模型
                self.log_message.emit("正在初始化背景替换模型...", "INFO")
                def progress_callback(current, total, message):
                    self.log_message.emit(f"模型初始化: {message} ({current}/{total})", "INFO")

                self.background_replacer.initialize_async(progress_callback)

                if not self.background_replacer.is_available():
                    error = self.background_replacer.get_initialization_error()
                    self.log_message.emit(f"背景替换模型初始化失败: {error}", "ERROR")
                    return False

            # 读取源人脸
            source_image = cv2.imread(str(self.source_path))
            if source_image is None:
                self.log_message.emit(f"无法读取源图像: {self.source_path}", "ERROR")
                return False

            # 检测源人脸
            self.log_message.emit("检测源图像中的人脸...", "INFO")
            source_faces = self.face_swapper.get_faces(source_image)
            if not source_faces:
                self.log_message.emit("源图像中未检测到人脸", "ERROR")
                return False

            source_face = source_faces[0]
            self.log_message.emit(f"源图像中检测到 {len(source_faces)} 个人脸，使用第一个", "INFO")

            # 打开视频
            cap = cv2.VideoCapture(str(self.target_path))
            if not cap.isOpened():
                self.log_message.emit(f"无法打开视频: {self.target_path}", "ERROR")
                return False

            # 获取视频属性
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            self.log_message.emit(f"视频属性信息: {width}x{height}, {fps}fps, {total_frames}帧", "INFO")

            # 确保输出目录存在
            output_file = Path(self.output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # 创建视频写入器
            if not str(self.output_path).endswith('.mp4'):
                self.output_path = str(self.output_path).rsplit('.', 1)[0] + '.mp4'

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(self.output_path), fourcc, fps, (width, height))

            if not out.isOpened():
                self.log_message.emit("无法创建视频写入器", "ERROR")
                cap.release()
                return False

            self.log_message.emit("视频写入器创建成功", "INFO")

            frame_count = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # 检查停止请求
                if self.stop_requested:
                    self.log_message.emit("收到停止请求，中断视频处理", "INFO")
                    break

                # 执行换脸
                result_frame = frame.copy()
                try:
                    target_faces = self.face_swapper.get_faces(frame)
                    if target_faces:
                        target_face = target_faces[0]  # 使用第一个检测到的人脸
                        swapped_frame = self.face_swapper.swap_face(source_image, frame, source_face, target_face)
                        if swapped_frame is not None:
                            result_frame = swapped_frame
                except Exception as e:
                    self.log_message.emit(f"帧 {frame_count}: 换脸失败: {e}", "WARNING")

                # 应用背景替换
                final_frame = self._apply_background_replacement(result_frame)
                if final_frame is None:
                    final_frame = result_frame  # 背景替换失败时使用换脸结果

                # 写入最终帧
                out.write(final_frame)

                frame_count += 1

                # 计算进度
                progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0

                # 每帧都发送进度更新（与原始逻辑保持一致）
                progress_text = f"处理视频(含背景替换): {frame_count}/{total_frames} 帧"
                self.progress_updated.emit(progress_text, int(progress))

                # 每帧都发送预览更新
                frame_info = f"帧 {frame_count}/{total_frames}"
                self.preview_updated.emit(frame, final_frame, frame_info)

                # 进度日志（与原始逻辑保持一致）
                if frame_count % 20 == 0 or progress in [5, 10, 25, 50, 75, 90, 100]:
                    log_msg = f"处理完成 {frame_count}/{total_frames} 帧 (含背景替换) - 已完成 {progress:.1f}%"
                    self.log_message.emit(log_msg, "INFO")

            # 释放资源
            cap.release()
            out.release()

            # 等待文件写入完成
            import time
            time.sleep(2.0)

            # 验证输出文件
            output_file = Path(self.output_path)
            if output_file.exists() and output_file.stat().st_size > 0:
                file_size_mb = output_file.stat().st_size / (1024 * 1024)
                self.log_message.emit(f"视频处理完成: {self.output_path}", "SUCCESS")
                self.log_message.emit(f"输出文件大小: {file_size_mb:.1f} MB", "INFO")
                self.log_message.emit(f"处理了 {frame_count} 帧（包含背景替换）", "INFO")

                # 保留音轨
                self.face_swapper._preserve_audio(self.target_path, self.output_path)

                return True
            else:
                self.log_message.emit("输出文件未生成或为空", "ERROR")
                return False

        except Exception as e:
            self.log_message.emit(f"视频处理失败: {e}", "ERROR")
            return False

    def _get_background_image(self):
        """获取背景图片"""
        try:
            if self.background_path:
                # 使用指定的背景图片
                background = cv2.imread(str(self.background_path))
                if background is not None:
                    return background
                else:
                    self.log_message.emit(f"无法读取背景图片: {self.background_path}", "ERROR")

            elif self.background_folder_path:
                # 从文件夹中随机选择背景图片
                background_file = self._get_random_background_from_folder()
                if background_file:
                    background = cv2.imread(background_file)
                    if background is not None:
                        self.log_message.emit(f"使用随机背景: {Path(background_file).name}", "INFO")
                        return background
                    else:
                        self.log_message.emit(f"无法读取随机背景图片: {background_file}", "ERROR")
                else:
                    self.log_message.emit("背景文件夹中没有可用的图片", "ERROR")

            return None

        except Exception as e:
            self.log_message.emit(f"获取背景图片失败: {e}", "ERROR")
            return None

    def _get_random_background_from_folder(self):
        """从背景文件夹中随机选择一张图片"""
        try:
            if not self.background_folder_path:
                return None

            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
            image_files = []

            for file_path in Path(self.background_folder_path).iterdir():
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    image_files.append(str(file_path))

            if image_files:
                import random
                return random.choice(image_files)
            return None

        except Exception as e:
            self.log_message.emit(f"从背景文件夹选择图片失败: {e}", "ERROR")
            return None

    def _process_image_with_background(self):
        """处理图像（包含背景替换）"""
        try:
            # 读取图像
            source_image = cv2.imread(str(self.source_path))
            target_image = cv2.imread(str(self.target_path))

            if source_image is None:
                self.log_message.emit(f"无法读取源图像: {self.source_path}", "ERROR")
                return False

            if target_image is None:
                self.log_message.emit(f"无法读取目标图像: {self.target_path}", "ERROR")
                return False

            # 执行换脸
            self.log_message.emit("开始执行换脸...", "INFO")
            result_image = self.face_swapper.swap_face(source_image, target_image)

            if result_image is None:
                self.log_message.emit("换脸失败", "ERROR")
                return False

            # 应用背景替换
            result_image = self._apply_background_replacement(result_image)

            # 保存结果
            success = cv2.imwrite(str(self.output_path), result_image)
            if not success:
                self.log_message.emit(f"保存图像失败: {self.output_path}", "ERROR")
                return False

            return True

        except Exception as e:
            self.log_message.emit(f"处理图像失败: {e}", "ERROR")
            return False
    
    def run(self):
        """运行处理"""
        try:
            if self.stop_requested:
                self.log_message.emit("处理已被用户停止", "WARNING")
                return
                
            target_ext = Path(self.target_path).suffix.lower()

            if target_ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv']:
                # 处理视频
                self.log_message.emit("开始处理视频文件...", "INFO")
                self.progress_updated.emit("正在处理视频...", 0)

                # 获取视频信息
                import cv2
                cap = cv2.VideoCapture(str(self.target_path))
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.release()

                self.log_message.emit(f"视频总帧数: {total_frames}", "INFO")

                # 创建进度回调
                def progress_callback(progress, current_frame, total_frames, extra_msg=None, original_frame=None, result_frame=None):
                    if self.stop_requested:
                        return False

                    # 更新进度
                    progress_text = f"处理视频: {current_frame}/{total_frames} 帧"
                    self.progress_updated.emit(progress_text, int(progress))

                    # 记录日志
                    if current_frame % 20 == 0 or progress in [5, 10, 25, 50, 75, 90, 100]:
                        log_msg = f"处理完成 {current_frame}/{total_frames} 帧 - 已完成 {progress:.1f}%"
                        self.log_message.emit(log_msg, "INFO")

                    # 如果有额外消息（如匹配度信息），也记录到日志
                    if extra_msg:
                        self.log_message.emit(extra_msg, "INFO")

                    # 发送预览更新
                    if original_frame is not None or result_frame is not None:
                        # 如果启用了背景替换，对预览的result_frame也应用背景替换
                        preview_result_frame = result_frame
                        if result_frame is not None and self.background_enabled and self.background_replacer:
                            try:
                                preview_result_frame = self._apply_background_replacement(result_frame)
                                if preview_result_frame is None:
                                    preview_result_frame = result_frame  # 背景替换失败时使用原图
                            except Exception as e:
                                self.log_message.emit(f"预览背景替换失败: {e}", "WARNING")
                                preview_result_frame = result_frame

                        frame_info = f"帧 {current_frame}/{total_frames}"
                        if extra_msg:
                            frame_info += f" - {extra_msg}"
                        self.preview_updated.emit(original_frame, preview_result_frame, frame_info)

                    return True

                # 如果启用了背景替换，需要使用自定义的视频处理流程
                if self.background_enabled and self.background_replacer:
                    success = self._process_video_with_background()
                else:
                    success = self.face_swapper.process_video(
                        self.source_path,
                        self.target_path,
                        self.output_path,
                        progress_callback=progress_callback,
                        stop_callback=lambda: self.stop_requested,
                        target_face_index=self.target_face_index,
                        selected_face_indices=self.selected_face_indices,
                        reference_frame_index=self.reference_frame_index
                    )
            else:
                # 处理图像
                self.log_message.emit("开始处理图像文件...", "INFO")
                self.progress_updated.emit("正在处理图像...", 50)

                if self.target_face_index is not None:
                    # 选择性换脸
                    self.log_message.emit(f"使用选择性换脸，目标人脸索引: {self.target_face_index}", "INFO")

                    # 读取图像
                    import cv2
                    source_image = cv2.imread(str(self.source_path))
                    target_image = cv2.imread(str(self.target_path))

                    if source_image is None or target_image is None:
                        self.log_message.emit("无法读取图像文件", "ERROR")
                        success = False
                    else:
                        # 执行选择性换脸
                        result_image = self.face_swapper.swap_face_selective(
                            source_image, target_image, self.target_face_index
                        )

                        if result_image is not None:
                            # 如果启用了背景替换，进行背景替换
                            if self.background_enabled and self.background_replacer:
                                result_image = self._apply_background_replacement(result_image)

                            # 保存结果
                            success = cv2.imwrite(str(self.output_path), result_image)
                            if success:
                                self.log_message.emit("选择性换脸成功", "SUCCESS")
                            else:
                                self.log_message.emit("保存结果图像失败", "ERROR")
                        else:
                            success = False
                            self.log_message.emit("选择性换脸失败", "ERROR")
                else:
                    # 普通换脸
                    if self.background_enabled and self.background_replacer:
                        # 使用自定义处理流程（包含背景替换）
                        success = self._process_image_with_background()
                    else:
                        # 使用原始处理流程
                        success = self.face_swapper.process_image(
                            self.source_path,
                            self.target_path,
                            self.output_path
                        )

                    if success:
                        self.log_message.emit("图像处理成功", "SUCCESS")
                    else:
                        self.log_message.emit("图像处理失败", "ERROR")

                self.progress_updated.emit("图像处理完成", 100)

            # 处理完成
            if self.stop_requested:
                self.progress_updated.emit("处理已停止", 0)
                self.log_message.emit("处理已被用户停止", "WARNING")
            elif success:
                self.progress_updated.emit("处理完成", 100)
                output_name = Path(self.output_path).name
                self.log_message.emit(f"换脸处理完成！输出文件: {output_name}", "SUCCESS")
            else:
                self.progress_updated.emit("处理失败", 0)
                self.log_message.emit("换脸处理失败", "ERROR")

            self.finished.emit(success and not self.stop_requested)

        except Exception as e:
            self.log_message.emit(f"处理过程中发生错误: {e}", "ERROR")
            self.finished.emit(False)

class ModernFaceSwapGUI(QMainWindow):
    """PyQt5现代化AI换脸GUI"""
    
    def __init__(self, gpu_config=None):
        super().__init__()

        # 初始化变量
        self.face_swapper = None
        self.source_path = None
        self.target_path = None
        self.output_path = None
        self.is_processing = False
        self.worker = None

        # 背景替换相关变量
        self.background_path = None
        self.background_folder_path = None

        # GPU配置
        self.gpu_config = gpu_config or {
            'gpu_available': False,
            'recommended_config': {},
            'force_cpu': False
        }

        # 设置窗口
        self.setWindowTitle("🎭 AI换脸【秘灵】")
        self.setGeometry(100, 100, 1600, 900)
        self.setMinimumSize(1400, 800)

        # 设置样式
        self._setup_styles()

        # 创建界面
        self._create_widgets()

        # 居中显示
        self._center_window()

        # 初始化GPU状态显示
        self._update_gpu_status()

        # 延迟刷新GPU状态（确保获取最新状态）
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1000, self._refresh_gpu_config)
    
    def _setup_styles(self):
        """设置现代化样式"""
        # 设置应用样式表
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #333333;
            }
            
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                min-height: 25px;
            }
            
            QPushButton:hover {
                background-color: #005a9e;
            }
            
            QPushButton:pressed {
                background-color: #004578;
            }
            
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            
            QPushButton#stopButton {
                background-color: #dc3545;
            }
            
            QPushButton#stopButton:hover {
                background-color: #c82333;
            }

            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 12px;
                background-color: white;
            }
            
            QLineEdit:focus {
                border-color: #007acc;
            }
            
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: #f8f9fa;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
            
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 4px;
                text-align: center;
                font-weight: bold;
            }
            
            QProgressBar::chunk {
                background-color: #007acc;
                border-radius: 2px;
            }
            
            QCheckBox {
                font-size: 14px;
                font-weight: bold;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            
            QCheckBox::indicator:unchecked {
                border: 2px solid #ddd;
                border-radius: 3px;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                border: 2px solid #4CAF50;
                border-radius: 3px;
                background-color: #4CAF50;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }

            QCheckBox::indicator:hover {
                border-color: #4CAF50;
            }

            QCheckBox::indicator:checked:hover {
                background-color: #45a049;
                border-color: #45a049;
            }
        """)
    
    def _center_window(self):
        """窗口居中显示"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def _create_widgets(self):
        """创建界面组件"""
        # 中央窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 0, 20)

        # 标题 - 设置固定高度，不参与自适应
        title_label = QLabel("🎭 AI换脸【秘灵】")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))  # 使用中文字体，减小字号
        title_label.setStyleSheet("color: #333333; margin: 0px; padding: 0px;")
        title_label.setFixedHeight(40)  # 设置固定高度，不参与自适应
        main_layout.addWidget(title_label)

        # 创建主水平分割器：左侧所有功能 | 右侧预览
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter, 1)  # 拉伸因子为1，占用剩余空间

        # 左侧：所有功能区域的垂直布局
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(15)

        # 文件选择区域 - 固定高度
        self._create_file_section(left_layout)

        # 控制面板 - 固定高度
        self._create_control_section(left_layout)

        # 日志和状态区域 - 自适应高度，占用剩余空间
        log_panel = self._create_log_status_panel()
        left_layout.addWidget(log_panel, 1)  # 拉伸因子为1，占用剩余空间

        main_splitter.addWidget(left_panel)

        # 右侧：预览区域（占据整个右侧高度）
        preview_panel = self._create_preview_panel()
        main_splitter.addWidget(preview_panel)

        # 设置分割比例 (左侧功能:右侧预览 = 3:2)
        main_splitter.setSizes([960, 640])

        # 底部状态栏
        self._create_status_bar(main_layout)

    def _create_status_bar(self, parent_layout):
        """创建底部状态栏"""
        # 状态栏容器 - 增加高度以容纳进度条
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                padding: 2px;
            }
        """)
        status_frame.setFixedHeight(60)  # 设置固定高度，不参与自适应

        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(8, 5, 8, 5)  # 增加垂直边距

        # 左侧：应用信息 - 增大字体到16px
        app_info_label = QLabel("🎭 AI换脸【秘灵】v1.0")
        app_info_label.setStyleSheet("color: #495057; font-weight: bold; font-size: 16px;")
        status_layout.addWidget(app_info_label)

        # 中间：弹性空间
        status_layout.addStretch()

        # 右侧进度区域（靠右显示）
        progress_layout = QHBoxLayout()

        # 进度标签
        progress_label = QLabel("进度：")
        progress_label.setStyleSheet("color: #495057; font-size: 16px; font-weight: 600;")
        progress_layout.addWidget(progress_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumWidth(250)
        self.progress_bar.setMaximumWidth(250)
        self.progress_bar.setMaximumHeight(18)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                font-size: 16px;
                background-color: #f8f9fa;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                border-radius: 7px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        # 状态文本（在进度条右侧）
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #495057; font-size: 16px; font-weight: 600; margin-left: 8px;")
        progress_layout.addWidget(self.status_label)

        status_layout.addLayout(progress_layout)

        # 右侧：系统状态和控制按钮
        right_status_layout = QHBoxLayout()

        # GPU加速选项
        self.gpu_checkbox = QCheckBox("🚀 GPU加速")
        self.gpu_checkbox.setChecked(False)
        self.gpu_checkbox.stateChanged.connect(self._on_gpu_checkbox_changed)
        self.gpu_checkbox.setStyleSheet("font-size: 16px; font-weight: 600;")
        right_status_layout.addWidget(self.gpu_checkbox)

        # GPU状态标签
        self.gpu_status_label = QLabel("检测中...")
        self.gpu_status_label.setStyleSheet("color: #666666; font-size: 16px; margin-right: 5px;")
        right_status_layout.addWidget(self.gpu_status_label)

        # GPU配置按钮
        self.gpu_config_button = QPushButton("🔧 一键配置GPU")
        self.gpu_config_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.gpu_config_button.clicked.connect(self._show_simple_gpu_install_dialog)
        right_status_layout.addWidget(self.gpu_config_button)

        # 性能优化按钮
        perf_btn = QPushButton("⚡ 性能优化")
        perf_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        perf_btn.setToolTip("🔧 性能优化设置")
        perf_btn.clicked.connect(self._show_performance_dialog)
        right_status_layout.addWidget(perf_btn)

        # GPU内存配置按钮
        self.gpu_memory_button = QPushButton("💾 内存限制")
        self.gpu_memory_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.gpu_memory_button.clicked.connect(self._show_gpu_memory_config)
        right_status_layout.addWidget(self.gpu_memory_button)



        status_layout.addLayout(right_status_layout)

        parent_layout.addWidget(status_frame)

        # 系统监控已移除，不再显示系统信息
        self.system_monitor = None
        self.enable_performance_monitoring = False

    def _create_file_section(self, parent_layout):
        """创建文件选择区域"""
        file_group = QGroupBox("📁 文件选择")
        file_group.setMinimumHeight(350)  # 增加最小高度，确保内容完整显示
        file_group.setMaximumHeight(380)  # 增加最大高度，保持稳定
        parent_layout.addWidget(file_group)

        layout = QGridLayout(file_group)
        layout.setSpacing(20)  # 进一步增加间距
        layout.setContentsMargins(20, 35, 20, 30)  # 增加更多内边距，利用控制面板节省的空间

        # 输入框通用样式
        input_style = """
            QLineEdit {
                padding: 8px 12px;
                font-size: 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-height: 20px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
        """

        # 浏览按钮通用样式
        browse_button_style = """
            QPushButton {
                padding: 8px 16px;
                font-size: 12px;
                min-width: 80px;
                max-width: 80px;
                min-height: 20px;
                border-radius: 4px;
            }
        """

        # 源人脸选择
        source_label = QLabel("源人脸图像:")
        source_label.setFont(QFont("Arial", 12))
        layout.addWidget(source_label, 0, 0)
        self.source_entry = QLineEdit()
        self.source_entry.setStyleSheet(input_style)
        self.source_entry.setPlaceholderText("选择源人脸图像文件...")
        layout.addWidget(self.source_entry, 0, 1)

        source_btn = QPushButton("浏览")
        source_btn.setStyleSheet(browse_button_style)
        source_btn.clicked.connect(self._select_source_file)
        layout.addWidget(source_btn, 0, 2, Qt.AlignLeft | Qt.AlignVCenter)

        # 目标文件选择
        target_label = QLabel("目标图像/视频:")
        target_label.setFont(QFont("Arial", 12))
        layout.addWidget(target_label, 1, 0)
        self.target_entry = QLineEdit()
        self.target_entry.setStyleSheet(input_style)
        self.target_entry.setPlaceholderText("选择目标图像或视频文件...")
        layout.addWidget(self.target_entry, 1, 1)

        target_btn = QPushButton("浏览")
        target_btn.setStyleSheet(browse_button_style)
        target_btn.clicked.connect(self._select_target_file)
        layout.addWidget(target_btn, 1, 2, Qt.AlignLeft | Qt.AlignVCenter)

        # 输出路径
        output_label = QLabel("输出路径:")
        output_label.setFont(QFont("Arial", 12))
        layout.addWidget(output_label, 2, 0)
        self.output_entry = QLineEdit()
        self.output_entry.setStyleSheet(input_style)
        self.output_entry.setPlaceholderText("自动生成输出路径...")
        layout.addWidget(self.output_entry, 2, 1)

        output_btn = QPushButton("选择")
        output_btn.setStyleSheet(browse_button_style)
        output_btn.clicked.connect(self._select_output_file)
        layout.addWidget(output_btn, 2, 2, Qt.AlignLeft | Qt.AlignVCenter)

        # 背景替换选项
        bg_label = QLabel("背景替换:")
        bg_label.setFont(QFont("Arial", 12))
        layout.addWidget(bg_label, 3, 0)

        # 背景替换勾选框和模式选择在同一行
        bg_row_layout = QHBoxLayout()
        bg_row_layout.setSpacing(10)

        self.background_checkbox = QCheckBox("启用背景替换")
        self.background_checkbox.setChecked(False)
        self.background_checkbox.stateChanged.connect(self._on_background_checkbox_changed)
        bg_row_layout.addWidget(self.background_checkbox)

        self.background_mode_combo = QComboBox()
        self.background_mode_combo.addItems([
            "BackgroundMattingV2 (推荐)",
            "MODNet (快速)",
            "U2Net (通用)",
            "Rembg (简单)"
        ])
        self.background_mode_combo.setEnabled(False)
        self.background_mode_combo.setMinimumWidth(200)
        self.background_mode_combo.currentTextChanged.connect(self._on_background_mode_changed)
        bg_row_layout.addWidget(self.background_mode_combo)

        # 模型状态标签
        self.background_status_label = QLabel("模型状态: 未检查")
        self.background_status_label.setStyleSheet("color: #666666; font-size: 12px;")
        self.background_status_label.setMinimumWidth(150)  # 设置最小宽度
        bg_row_layout.addWidget(self.background_status_label)

        # 下载模型按钮
        self.download_model_btn = QPushButton("下载模型")
        self.download_model_btn.setEnabled(False)
        self.download_model_btn.setVisible(False)
        self.download_model_btn.clicked.connect(self._download_background_model)
        self.download_model_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        bg_row_layout.addWidget(self.download_model_btn)

        bg_row_layout.addStretch()  # 添加弹性空间

        bg_row_widget = QWidget()
        bg_row_widget.setLayout(bg_row_layout)
        layout.addWidget(bg_row_widget, 3, 1, 1, 2)  # 跨越两列，增加宽度

        # 背景图片/文件夹选择
        bg_source_label = QLabel("背景来源:")
        bg_source_label.setFont(QFont("Arial", 12))
        layout.addWidget(bg_source_label, 4, 0)

        self.background_entry = QLineEdit()
        self.background_entry.setStyleSheet(input_style)
        self.background_entry.setPlaceholderText("选择背景图片或文件夹...")
        self.background_entry.setEnabled(False)
        layout.addWidget(self.background_entry, 4, 1)

        # 统一的背景选择按钮
        self.bg_select_btn = QPushButton("选择背景")
        self.bg_select_btn.setStyleSheet(browse_button_style)
        self.bg_select_btn.clicked.connect(self._select_background)
        self.bg_select_btn.setEnabled(False)
        self.bg_select_btn.setMinimumWidth(100)
        layout.addWidget(self.bg_select_btn, 4, 2, Qt.AlignLeft | Qt.AlignVCenter)

        # 设置列宽比例 - 给按钮列更多空间
        layout.setColumnStretch(0, 0)  # 标签列固定宽度
        layout.setColumnStretch(1, 2)  # 输入框列
        layout.setColumnStretch(2, 1)  # 按钮列

    def _create_control_section(self, parent_layout):
        """创建控制面板"""
        control_group = QGroupBox("🎛️ 控制面板")
        control_group.setMinimumHeight(80)  # 设置固定最小高度
        control_group.setMaximumHeight(100)  # 设置最大高度，保持紧凑
        parent_layout.addWidget(control_group)

        # 使用垂直布局来创建两行
        main_layout = QVBoxLayout(control_group)
        main_layout.setContentsMargins(20, 25, 20, 20)
        main_layout.setSpacing(10)

        # 第一行：主要操作按钮（缩小按钮尺寸）
        first_row = QHBoxLayout()

        # 按钮通用样式 - 增大字体到16px
        button_style = """
            QPushButton {
                padding: 6px 10px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 4px;
                min-height: 32px;
                max-height: 36px;
                min-width: 90px;
                max-width: 140px;
            }
        """

        # 初始化AI按钮
        self.init_button = QPushButton("🤖 初始化AI")
        self.init_button.setStyleSheet(button_style)
        self.init_button.clicked.connect(self._manual_init_ai)
        first_row.addWidget(self.init_button)

        # 开始按钮
        self.start_button = QPushButton("🚀 开始换脸")
        self.start_button.setStyleSheet(button_style)
        self.start_button.clicked.connect(self._start_face_swap)
        self.start_button.setEnabled(False)
        first_row.addWidget(self.start_button)

        # 停止按钮
        self.stop_button = QPushButton("⏹ 停止")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setStyleSheet(button_style)
        self.stop_button.clicked.connect(self._stop_face_swap)
        self.stop_button.setEnabled(False)
        first_row.addWidget(self.stop_button)

        # 打开文件夹按钮
        folder_btn = QPushButton("📁 打开输出文件夹")
        folder_btn.setStyleSheet(button_style)
        folder_btn.clicked.connect(self._open_output_folder)
        first_row.addWidget(folder_btn)

        # 多人脸选择选项 - 直接添加到按钮行，节省空间
        self.multi_face_checkbox = QCheckBox("🎯 多人脸选择")
        self.multi_face_checkbox.setChecked(False)
        self.multi_face_checkbox.setStyleSheet("margin-left: 15px; font-size: 16px;")
        first_row.addWidget(self.multi_face_checkbox)

        # 添加弹性空间，让控件左对齐
        first_row.addStretch()

        main_layout.addLayout(first_row)

    def _on_gpu_checkbox_changed(self, state):
        """GPU选项状态改变时的处理"""
        if state == 2:  # 选中状态
            # 如果GPU不可用但用户尝试开启，显示配置向导
            if not self.gpu_config.get('gpu_available', False):
                self._show_gpu_unavailable_dialog()
                self.gpu_checkbox.setChecked(False)  # 重置为未选中

    def _show_gpu_unavailable_dialog(self):
        """显示GPU不可用对话框"""
        from PyQt5.QtWidgets import QMessageBox

        reason = self.gpu_config.get('recommended_config', {}).get('reason', '未知原因')

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("GPU加速不可用")
        msg.setText("GPU加速当前不可用")
        msg.setInformativeText(f"原因: {reason}\n\n是否要打开GPU配置向导进行自动配置？")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)

        if msg.exec_() == QMessageBox.Yes:
            self._open_gpu_config_wizard()

    def _open_gpu_config_wizard(self):
        """打开GPU配置向导"""
        try:
            from gui.gpu_config_wizard import GPUConfigWizard
            wizard = GPUConfigWizard(self.gpu_config, self)
            if wizard.exec_() == wizard.Accepted:
                # 配置完成，重新检测GPU环境
                self._refresh_gpu_config()
        except ImportError:
            # 如果没有GPU配置向导，使用简单的安装对话框
            self._show_simple_gpu_install_dialog()

    def _show_simple_gpu_install_dialog(self):
        """显示简单的GPU安装对话框"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel
        import subprocess
        import sys

        # 创建自定义对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("🚀 一键GPU配置")
        dialog.setMinimumSize(500, 400)

        layout = QVBoxLayout()

        # 说明文本
        info_label = QLabel("🎯 智能GPU配置助手")
        info_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(info_label)

        desc_label = QLabel("将自动检测您的硬件环境并安装最适合的GPU加速组件：\n"
                           "• 🚀 NVIDIA GPU → 安装CUDA支持 (最佳性能)\n"
                           "• ⚡ AMD/Intel GPU → 安装DirectML支持 (良好性能)\n"
                           "• 💻 其他情况 → 确保CPU支持 (兼容性最佳)\n\n"
                           "整个过程大约需要2-5分钟，请保持网络连接。")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("margin: 10px; color: #666;")
        layout.addWidget(desc_label)

        # 日志显示区域
        self.install_log_text = QTextEdit()
        self.install_log_text.setReadOnly(True)
        self.install_log_text.setMaximumHeight(200)
        self.install_log_text.setStyleSheet("background-color: #f5f5f5; font-family: monospace;")
        layout.addWidget(self.install_log_text)

        # 按钮
        button_layout = QHBoxLayout()

        self.start_install_btn = QPushButton("🚀 开始配置")
        self.start_install_btn.clicked.connect(lambda: self._start_one_click_install(dialog))
        button_layout.addWidget(self.start_install_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)

        # 显示对话框
        dialog.exec_()

    def _start_one_click_install(self, dialog):
        """开始一键安装"""
        from PyQt5.QtCore import QThread, pyqtSignal
        import subprocess
        import sys

        self.start_install_btn.setEnabled(False)
        self.start_install_btn.setText("⏳ 配置中...")
        self.install_log_text.clear()
        self.install_log_text.append("🚀 开始一键GPU配置...\n")

        # 创建安装线程
        class OneClickInstallThread(QThread):
            log_signal = pyqtSignal(str)
            finished_signal = pyqtSignal(bool, str)

            def run(self):
                try:
                    # 使用一键配置脚本
                    process = subprocess.Popen([
                        sys.executable, 'scripts/one_click_gpu_setup.py'
                    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, bufsize=1, universal_newlines=True)

                    # 实时读取输出
                    output_lines = []
                    for line in process.stdout:
                        line = line.strip()
                        if line:
                            self.log_signal.emit(line)
                            output_lines.append(line)

                    process.wait()
                    success = process.returncode == 0
                    full_output = '\n'.join(output_lines)

                    self.finished_signal.emit(success, full_output)

                except Exception as e:
                    self.finished_signal.emit(False, str(e))

        # 启动安装线程
        self.install_thread = OneClickInstallThread()
        self.install_thread.log_signal.connect(self.install_log_text.append)
        self.install_thread.finished_signal.connect(lambda success, msg: self._on_one_click_install_finished(success, msg, dialog))
        self.install_thread.start()

    def _on_one_click_install_finished(self, success, message, dialog):
        """一键安装完成回调"""
        from PyQt5.QtWidgets import QMessageBox

        self.start_install_btn.setEnabled(True)
        self.start_install_btn.setText("🚀 开始配置")

        if success:
            self.install_log_text.append("\n🎉 GPU配置完成!")
            QMessageBox.information(dialog, "配置完成",
                                  "🎉 GPU配置完成！\n\n请重启程序以使用GPU加速功能。")
            dialog.accept()
            # 重新检测GPU环境
            self._refresh_gpu_config()
        else:
            self.install_log_text.append(f"\n❌ 配置失败: {message}")
            QMessageBox.critical(dialog, "配置失败",
                               f"❌ GPU配置失败\n\n错误信息:\n{message}\n\n请检查网络连接或手动配置。")



    def _refresh_gpu_config(self):
        """刷新GPU配置"""
        try:
            # 重新检测GPU环境
            from main_pyqt import check_gpu_environment
            gpu_result = check_gpu_environment()

            # 更新GPU配置
            self.gpu_config = {
                'gpu_available': gpu_result.get('gpu_available', False),
                'recommended_config': gpu_result.get('recommended_config', {}),
                'force_cpu': False
            }

            # 更新界面显示
            self._update_gpu_status()

            self._log_message("GPU配置已刷新", "INFO")
        except Exception as e:
            self._log_message(f"刷新GPU配置失败: {e}", "ERROR")

    def _init_system_monitor(self):
        """初始化系统监控器（单例模式）"""
        try:
            from utils.system_monitor import SystemMonitor
            self.system_monitor = SystemMonitor()
            # 不启动后台监控线程，避免额外开销
        except Exception as e:
            print(f"系统监控器初始化失败: {e}")
            self.system_monitor = None

    def _show_static_system_info(self):
        """显示静态系统信息（不实时更新）"""
        try:
            import psutil
            import platform

            # 获取基本系统信息
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            memory_gb = round(memory.total / (1024**3), 1)

            # 检查GPU状态
            gpu_status = "GPU: 未知"
            try:
                import onnxruntime as ort
                providers = ort.get_available_providers()
                if 'CUDAExecutionProvider' in providers:
                    gpu_status = "GPU: CUDA可用"
                elif 'DmlExecutionProvider' in providers:
                    gpu_status = "GPU: DirectML可用"
                else:
                    gpu_status = "GPU: 仅CPU"
            except:
                gpu_status = "GPU: 检测失败"

            # 组合状态文本
            status_text = f"{gpu_status} | CPU: {cpu_count}核 | 内存: {memory_gb}GB"

            if hasattr(self, 'system_status_label'):
                self.system_status_label.setText(status_text)
                self.system_status_label.setStyleSheet("""
                    color: #495057;
                    font-size: 13px;
                    font-weight: 600;
                    padding: 4px 10px;
                    background-color: #e9ecef;
                    border-radius: 4px;
                    border: 1px solid #ced4da;
                """)

        except Exception as e:
            if hasattr(self, 'system_status_label'):
                self.system_status_label.setText("系统: 信息获取失败")
                self.system_status_label.setStyleSheet("""
                    color: #6c757d;
                    font-size: 13px;
                    font-weight: 600;
                    padding: 4px 10px;
                    background-color: #e9ecef;
                    border-radius: 4px;
                    border: 1px solid #ced4da;
                """)

    def _update_system_status(self):
        """更新系统状态显示（优化版本）"""
        try:
            # 使用单例监控器，避免重复创建
            if not hasattr(self, 'system_monitor') or self.system_monitor is None:
                self._init_system_monitor()

            if self.system_monitor is None:
                raise Exception("系统监控器不可用")

            info = self.system_monitor.get_all_info()

            # 格式化状态文本
            gpu_status = monitor.format_gpu_status(info['gpu'])
            cpu_status = monitor.format_cpu_status(info['cpu'])
            memory_status = monitor.format_memory_status(info['memory'])

            # 组合状态文本
            status_text = f"{gpu_status} | {cpu_status} | {memory_status}"

            # 根据GPU使用率设置颜色
            color = "#6c757d"  # 默认灰色
            if info['gpu'].get('available') and info['gpu'].get('gpus'):
                gpu_usage = info['gpu']['gpus'][0]['utilization_percent']
                if gpu_usage > 50:
                    color = "#28a745"  # 绿色 - 高使用率
                elif gpu_usage > 10:
                    color = "#007bff"  # 蓝色 - 中等使用率
                elif gpu_usage > 0:
                    color = "#fd7e14"  # 橙色 - 低使用率
                else:
                    color = "#6c757d"  # 灰色 - 待机

            # 更新显示 - 只在内容变化时更新，减少卡顿
            if hasattr(self, 'system_status_label'):
                # 检查是否需要更新（避免不必要的重绘）
                current_text = self.system_status_label.text()
                if current_text != status_text:
                    self.system_status_label.setText(status_text)
                    self.system_status_label.setStyleSheet(f"""
                        color: {color};
                        font-size: 13px;
                        font-weight: 600;
                        padding: 4px 10px;
                        background-color: #e9ecef;
                        border-radius: 4px;
                        border: 1px solid #ced4da;
                    """)
                    # 只在内容变化时刷新
                    self.system_status_label.update()

        except Exception as e:
            # 如果监控失败，显示基本信息 - 增大字体
            if hasattr(self, 'system_status_label'):
                self.system_status_label.setText("系统: 监控不可用")
                self.system_status_label.setStyleSheet("""
                    color: #dc3545;
                    font-size: 13px;
                    font-weight: 600;
                    padding: 4px 10px;
                    background-color: #f8d7da;
                    border-radius: 4px;
                    border: 1px solid #f5c6cb;
                """)

    def _show_gpu_memory_config(self):
        """显示GPU内存配置对话框"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QCheckBox, QSpinBox, QGroupBox, QFormLayout
        from PyQt5.QtCore import Qt

        # 加载当前配置
        try:
            from scripts.gpu_memory_config import load_config, save_config
            config = load_config()
        except:
            config = {
                "memory_limit_percent": 90,
                "memory_check_interval": 10,
                "auto_fallback_enabled": True,
                "max_gpu_errors": 5
            }

        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("💾 GPU内存配置")
        dialog.setMinimumSize(400, 300)

        layout = QVBoxLayout(dialog)

        # 标题
        title_label = QLabel("🎛️ GPU内存使用配置")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)

        # 内存限制配置
        memory_group = QGroupBox("内存使用限制")
        memory_layout = QFormLayout(memory_group)

        # 内存限制滑块
        memory_slider = QSlider(Qt.Horizontal)
        memory_slider.setRange(50, 98)
        memory_slider.setValue(config['memory_limit_percent'])
        memory_slider.setTickPosition(QSlider.TicksBelow)
        memory_slider.setTickInterval(10)

        memory_value_label = QLabel(f"{config['memory_limit_percent']}%")
        memory_value_label.setStyleSheet("font-weight: bold; color: #2196F3;")

        def update_memory_label(value):
            memory_value_label.setText(f"{value}%")

        memory_slider.valueChanged.connect(update_memory_label)

        memory_h_layout = QHBoxLayout()
        memory_h_layout.addWidget(memory_slider)
        memory_h_layout.addWidget(memory_value_label)

        memory_layout.addRow("GPU内存使用限制:", memory_h_layout)

        # 检查间隔
        interval_spinbox = QSpinBox()
        interval_spinbox.setRange(1, 50)
        interval_spinbox.setValue(config['memory_check_interval'])
        interval_spinbox.setSuffix(" 帧")
        memory_layout.addRow("内存检查间隔:", interval_spinbox)

        layout.addWidget(memory_group)

        # 自动回退配置
        fallback_group = QGroupBox("自动回退设置")
        fallback_layout = QFormLayout(fallback_group)

        # 自动回退开关
        auto_fallback_checkbox = QCheckBox("启用自动回退到CPU")
        auto_fallback_checkbox.setChecked(config['auto_fallback_enabled'])
        fallback_layout.addRow(auto_fallback_checkbox)

        # 最大错误次数
        max_errors_spinbox = QSpinBox()
        max_errors_spinbox.setRange(1, 20)
        max_errors_spinbox.setValue(config['max_gpu_errors'])
        max_errors_spinbox.setSuffix(" 次")
        fallback_layout.addRow("最大GPU错误次数:", max_errors_spinbox)

        layout.addWidget(fallback_group)

        # 按钮
        button_layout = QHBoxLayout()

        # 重置按钮
        reset_btn = QPushButton("🔄 重置默认")
        reset_btn.clicked.connect(lambda: self._reset_memory_config(memory_slider, interval_spinbox, auto_fallback_checkbox, max_errors_spinbox))
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()

        # 取消按钮
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        # 保存按钮
        save_btn = QPushButton("✅ 保存")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;")
        save_btn.clicked.connect(lambda: self._save_memory_config(
            dialog, memory_slider.value(), interval_spinbox.value(),
            auto_fallback_checkbox.isChecked(), max_errors_spinbox.value()
        ))
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

        dialog.exec_()

    def _reset_memory_config(self, memory_slider, interval_spinbox, auto_fallback_checkbox, max_errors_spinbox):
        """重置内存配置为默认值"""
        memory_slider.setValue(90)
        interval_spinbox.setValue(10)
        auto_fallback_checkbox.setChecked(True)
        max_errors_spinbox.setValue(5)

    def _save_memory_config(self, dialog, memory_limit, check_interval, auto_fallback, max_errors):
        """保存内存配置"""
        try:
            from scripts.gpu_memory_config import save_config

            config = {
                "memory_limit_percent": memory_limit,
                "memory_check_interval": check_interval,
                "auto_fallback_enabled": auto_fallback,
                "max_gpu_errors": max_errors
            }

            if save_config(config):
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(dialog, "配置保存成功",
                                      f"✅ GPU内存配置已保存！\n\n"
                                      f"内存限制: {memory_limit}%\n"
                                      f"检查间隔: 每{check_interval}帧\n"
                                      f"自动回退: {'启用' if auto_fallback else '禁用'}\n"
                                      f"最大错误: {max_errors}次\n\n"
                                      f"配置将在下次处理时生效。")
                dialog.accept()
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(dialog, "保存失败", "❌ 配置保存失败，请检查文件权限。")
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(dialog, "保存失败", f"❌ 配置保存失败: {e}")

    def _update_gpu_usage_status(self, status_text, color="#888888"):
        """更新GPU使用状态显示（兼容性方法）"""
        # 这个方法现在由_update_system_status替代，但保留以兼容现有代码
        pass

    def _update_gpu_status(self):
        """更新GPU状态显示"""
        if not hasattr(self, 'gpu_status_label'):
            return

        gpu_available = self.gpu_config.get('gpu_available', False)
        recommended_config = self.gpu_config.get('recommended_config', {})
        force_cpu = self.gpu_config.get('force_cpu', False)

        if force_cpu:
            # 强制CPU模式
            self.gpu_checkbox.setChecked(False)
            self.gpu_checkbox.setEnabled(False)
            self.gpu_status_label.setText("强制CPU模式")
            self.gpu_status_label.setStyleSheet("color: #ff6b6b; font-size: 11px;")
            self.gpu_config_button.setVisible(False)

        elif gpu_available:
            # GPU可用
            provider = recommended_config.get('provider', 'Unknown')
            description = recommended_config.get('description', 'GPU加速')
            performance = recommended_config.get('performance', 'unknown')

            self.gpu_checkbox.setChecked(True)
            self.gpu_checkbox.setEnabled(True)
            self.gpu_config_button.setVisible(False)

            # 根据性能等级设置颜色
            if performance == 'excellent':
                color = "#51cf66"  # 绿色
                icon = "🚀"
            elif performance == 'good':
                color = "#74c0fc"  # 蓝色
                icon = "⚡"
            else:
                color = "#ffd43b"  # 黄色
                icon = "🔧"

            status_text = f"{icon} {description}"
            self.gpu_status_label.setText(status_text)
            self.gpu_status_label.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")

            # 设置详细的工具提示
            tooltip = f"GPU加速状态: 可用\n"
            tooltip += f"提供者: {provider}\n"
            tooltip += f"性能等级: {performance}\n"
            tooltip += f"原因: {recommended_config.get('reason', '未知')}"
            self.gpu_checkbox.setToolTip(tooltip)

        else:
            # GPU不可用 - 显示配置按钮
            reason = recommended_config.get('reason', '未知原因')

            self.gpu_checkbox.setChecked(False)
            self.gpu_checkbox.setEnabled(False)
            self.gpu_status_label.setText("❌ GPU不可用")
            self.gpu_status_label.setStyleSheet("color: #ff6b6b; font-size: 11px;")
            self.gpu_config_button.setVisible(True)  # 显示配置按钮

            # 设置详细的工具提示
            tooltip = f"GPU加速状态: 不可用\n"
            tooltip += f"原因: {reason}\n"
            tooltip += f"点击'配置GPU'按钮进行一键配置"
            self.gpu_checkbox.setToolTip(tooltip)

    def _create_log_status_panel(self):
        """创建日志和状态面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)  # 移除外层边距
        layout.setSpacing(0)  # 移除间距

        # 日志区域 - 减小边框和内边距
        log_group = QGroupBox("📋 执行日志")

        log_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 5px 0 5px;
            }
        """)
        layout.addWidget(log_group)

        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(15, 15, 15, 15)  # 与上方模块保持一致的内边距

        self.log_text = QTextEdit()
        # 让日志区域自适应高度，撑满剩余空间
        self.log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 设置日志文字样式和滚动
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                line-height: 1.2;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px;
                background-color: #fafafa;
            }
        """)

        # 确保自动滚动到底部
        self.log_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.log_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        log_layout.addWidget(self.log_text)

        # 初始日志
        self._log_message("=== AI换脸应用程序日志 ===", "INFO")
        self._log_message("点击'🤖 初始化AI'开始使用", "INFO")

        # 移除状态栏，进度条已移至底部状态栏

        return panel

    def _create_preview_panel(self):
        """创建预览面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 预览区域标题
        preview_group = QGroupBox("🖼️ 实时预览")
        layout.addWidget(preview_group)

        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(20, 25, 20, 20)

        # 创建水平布局放置两个预览图（左右排列）
        images_layout = QHBoxLayout()
        preview_layout.addLayout(images_layout)

        # 原图预览
        original_group = QGroupBox("原图")
        original_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        images_layout.addWidget(original_group)
        original_layout = QVBoxLayout(original_group)
        original_layout.setContentsMargins(5, 5, 5, 5)

        self.original_preview = QLabel()
        self.original_preview.setMinimumSize(280, 200)
        # 移除最大高度限制，让其自适应撑满
        self.original_preview.setAlignment(Qt.AlignCenter)
        self.original_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.original_preview.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 8px;
                background-color: #f8f9fa;
                color: #666;
            }
        """)
        self.original_preview.setText("原图预览\n等待处理...")
        original_layout.addWidget(self.original_preview)

        # 换脸后预览
        result_group = QGroupBox("换脸后")
        result_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        images_layout.addWidget(result_group)
        result_layout = QVBoxLayout(result_group)
        result_layout.setContentsMargins(5, 5, 5, 5)

        self.result_preview = QLabel()
        self.result_preview.setMinimumSize(280, 200)
        # 移除最大高度限制，让其自适应撑满
        self.result_preview.setAlignment(Qt.AlignCenter)
        self.result_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.result_preview.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                color: #666;
            }
        """)
        self.result_preview.setText("换脸预览\n等待处理...")
        result_layout.addWidget(self.result_preview)

        # 预览信息
        self.preview_info = QLabel("等待开始处理...")
        self.preview_info.setAlignment(Qt.AlignCenter)
        self.preview_info.setStyleSheet("color: #666; font-size: 12px;")
        self.preview_info.setMaximumHeight(30)  # 限制信息区域高度
        self.preview_info.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        preview_layout.addWidget(self.preview_info)

        return panel

    def _update_preview(self, original_frame, result_frame, frame_info=""):
        """更新预览图像"""
        try:
            # 更新原图预览
            if original_frame is not None:
                original_pixmap = self._cv2_to_pixmap(original_frame)
                if original_pixmap:
                    scaled_pixmap = original_pixmap.scaled(
                        self.original_preview.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.original_preview.setPixmap(scaled_pixmap)

            # 更新换脸后预览
            if result_frame is not None:
                result_pixmap = self._cv2_to_pixmap(result_frame)
                if result_pixmap:
                    scaled_pixmap = result_pixmap.scaled(
                        self.result_preview.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.result_preview.setPixmap(scaled_pixmap)

            # 更新预览信息
            if frame_info:
                self.preview_info.setText(frame_info)

        except Exception as e:
            print(f"预览更新失败: {e}")

    def _cv2_to_pixmap(self, cv_img):
        """将OpenCV图像转换为QPixmap"""
        try:
            if cv_img is None:
                return None

            # 转换BGR到RGB
            rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w

            # 创建QImage
            from PyQt5.QtGui import QImage
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

            # 转换为QPixmap
            return QPixmap.fromImage(qt_image)

        except Exception as e:
            print(f"图像转换失败: {e}")
            return None

    def _log_message(self, message, level="INFO"):
        """添加日志消息"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # 根据级别设置前缀和颜色
        if level == "ERROR":
            prefix = "❌"
            color = "#dc3545"
        elif level == "WARNING":
            prefix = "⚠️"
            color = "#ffc107"
        elif level == "SUCCESS":
            prefix = "✅"
            color = "#28a745"
        else:
            prefix = "ℹ️"
            color = "#333333"

        log_line = f'<span style="color: {color};">[{timestamp}] {prefix} {message}</span><br>'

        # 添加到日志框并自动滚动到底部
        self.log_text.insertHtml(log_line)

        # 确保滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        # 移动光标到末尾
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)

    def _update_status(self, text):
        """更新状态"""
        self.status_label.setText(text)

    def _update_progress(self, text, progress):
        """更新进度"""
        self._update_status(text)
        self.progress_bar.setValue(progress)

    def _select_source_file(self):
        """选择源人脸文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择源人脸图像",
            "",
            "图像文件 (*.jpg *.jpeg *.png *.bmp *.tiff);;所有文件 (*.*)"
        )

        if file_path:
            self.source_path = file_path
            self.source_entry.setText(file_path)
            self._update_status(f"已选择源人脸: {Path(file_path).name}")
            self._log_message(f"已选择源人脸图像: {Path(file_path).name}")
            self._check_ready_to_start()

    def _select_target_file(self):
        """选择目标文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择目标图像或视频",
            "",
            "所有支持的文件 (*.jpg *.jpeg *.png *.bmp *.tiff *.mp4 *.avi *.mov *.mkv *.wmv);;"
            "图像文件 (*.jpg *.jpeg *.png *.bmp *.tiff);;"
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv);;"
            "所有文件 (*.*)"
        )

        if file_path:
            self.target_path = file_path
            self.target_entry.setText(file_path)

            # 自动设置输出路径
            self._auto_set_output_path(file_path)
            self._update_status(f"已选择目标文件: {Path(file_path).name}")
            self._log_message(f"已选择目标文件: {Path(file_path).name}")
            self._check_ready_to_start()

    def _select_output_file(self):
        """选择输出文件"""
        if not self.target_path:
            QMessageBox.warning(self, "提示", "请先选择目标文件")
            return

        target_ext = Path(self.target_path).suffix
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择输出路径",
            "",
            f"视频文件 (*.mp4)" if target_ext.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
            else f"图像文件 (*.jpg);;所有文件 (*.*)"
        )

        if file_path:
            self.output_path = file_path
            self.output_entry.setText(file_path)
            self._update_status(f"输出路径: {Path(file_path).name}")
            self._check_ready_to_start()

    def _auto_set_output_path(self, target_path):
        """自动设置输出路径"""
        target_file = Path(target_path)
        output_dir = Path("face_swap_results").absolute()  # 使用绝对路径
        output_dir.mkdir(exist_ok=True)

        # 生成输出文件名
        stem = target_file.stem
        ext = target_file.suffix

        # 如果是视频文件，使用.mp4格式
        if ext.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.wmv']:
            output_name = f"{stem}_face_swapped.mp4"
        else:
            output_name = f"{stem}_face_swapped{ext}"

        output_path = output_dir / output_name

        self.output_path = str(output_path.absolute())  # 使用绝对路径
        self.output_entry.setText(str(output_path.absolute()))

    def _check_ready_to_start(self):
        """检查是否准备好开始处理"""
        try:
            # 安全检查所有条件
            has_source = bool(self.source_path) and Path(str(self.source_path)).exists() if self.source_path else False
            has_target = bool(self.target_path) and Path(str(self.target_path)).exists() if self.target_path else False
            has_output = bool(self.output_path) if self.output_path else False
            has_swapper = self.face_swapper is not None

            # 检查背景替换设置
            background_ready = True
            if hasattr(self, 'background_checkbox') and self.background_checkbox.isChecked():
                has_background = bool(self.background_path or self.background_folder_path)
                if not has_background:
                    background_ready = False

            # 确保ready是布尔值
            ready = bool(has_source and has_target and has_output and has_swapper and background_ready)

            # 安全更新按钮状态
            if hasattr(self, 'start_button') and self.start_button is not None:
                self.start_button.setEnabled(ready)

            # 更新状态文字
            if ready:
                self._update_status("准备就绪 - 可以开始换脸")
            else:
                if not has_swapper:
                    self._update_status("请先初始化AI模型")
                elif not has_source:
                    self._update_status("请选择源人脸图像")
                elif not has_target:
                    self._update_status("请选择目标文件")
                elif not has_output:
                    self._update_status("请设置输出路径")
                elif not background_ready:
                    self._update_status("请选择背景图片或文件夹")

        except Exception as e:
            print(f"_check_ready_to_start error: {e}")
            # 发生错误时禁用按钮
            if hasattr(self, 'start_button') and self.start_button is not None:
                self.start_button.setEnabled(False)
            self._update_status("状态检查错误")

    def _manual_init_ai(self):
        """手动初始化AI"""
        if self.face_swapper is not None:
            QMessageBox.information(self, "提示", "AI已经初始化完成")
            return

        # 禁用初始化按钮
        self.init_button.setEnabled(False)
        self.init_button.setText("初始化中...")

        # 开始初始化
        self._initialize_face_swapper()

    def _initialize_face_swapper(self):
        """初始化换脸引擎"""
        # 创建初始化工作线程
        class InitWorker(QThread):
            status_updated = pyqtSignal(str)
            log_message = pyqtSignal(str, str)
            init_finished = pyqtSignal(bool, str, object)  # 成功/失败, 错误消息, face_swapper对象

            def __init__(self, use_gpu):
                super().__init__()
                self.use_gpu = use_gpu
                self.face_swapper = None

            def run(self):
                try:
                    self.status_updated.emit("正在初始化AI模型...")
                    self.log_message.emit("开始初始化AI模型...", "INFO")

                    # 详细的GPU状态日志
                    if self.use_gpu:
                        self.log_message.emit("⚡ GPU加速: 启用", "INFO")
                        try:
                            import onnxruntime as ort
                            providers = ort.get_available_providers()
                            self.log_message.emit(f"📋 可用提供者: {', '.join(providers)}", "INFO")

                            if 'CUDAExecutionProvider' in providers:
                                self.log_message.emit("🚀 使用CUDA GPU加速", "SUCCESS")
                                # 更新GPU状态显示
                                if hasattr(self.parent(), '_update_gpu_usage_status'):
                                    self.parent()._update_gpu_usage_status("CUDA处理中", "#4CAF50")
                            elif 'DmlExecutionProvider' in providers:
                                self.log_message.emit("⚡ 使用DirectML GPU加速", "SUCCESS")
                                # 更新GPU状态显示
                                if hasattr(self.parent(), '_update_gpu_usage_status'):
                                    self.parent()._update_gpu_usage_status("DirectML处理中", "#2196F3")
                            else:
                                self.log_message.emit("⚠️ GPU提供者不可用，将回退到CPU", "WARNING")
                                # 更新CPU状态显示
                                if hasattr(self.parent(), '_update_gpu_usage_status'):
                                    self.parent()._update_gpu_usage_status("CPU处理中", "#FF9800")
                        except Exception as e:
                            self.log_message.emit(f"❌ GPU检测失败: {e}", "ERROR")
                    else:
                        self.log_message.emit("💻 GPU加速: 禁用 (使用CPU模式)", "INFO")
                        # 更新CPU状态显示
                        if hasattr(self.parent(), '_update_gpu_usage_status'):
                            self.parent()._update_gpu_usage_status("CPU模式", "#FF9800")

                    self.face_swapper = FaceSwapper(use_gpu=self.use_gpu)

                    self.status_updated.emit("AI模型初始化完成，就绪")
                    self.log_message.emit("✅ AI模型初始化完成", "SUCCESS")
                    self.init_finished.emit(True, "", self.face_swapper)

                except Exception as e:
                    error_msg = str(e)
                    self.status_updated.emit(f"模型初始化失败: {error_msg}")
                    self.log_message.emit(f"模型初始化失败: {error_msg}", "ERROR")
                    self.init_finished.emit(False, error_msg, None)

        # 创建工作线程
        use_gpu = self.gpu_checkbox.isChecked()
        self.init_worker = InitWorker(use_gpu)

        # 连接信号
        self.init_worker.status_updated.connect(self._update_status)
        self.init_worker.log_message.connect(self._log_message)
        self.init_worker.init_finished.connect(self._on_init_finished)

        # 开始初始化
        self.init_worker.start()

    def _on_init_finished(self, success, error_msg, face_swapper):
        """初始化完成回调"""
        try:
            if success and face_swapper is not None:
                self.face_swapper = face_swapper
                if hasattr(self, 'init_button') and self.init_button is not None:
                    self.init_button.setText("✅ AI已就绪")
                    self.init_button.setEnabled(False)
                self._check_ready_to_start()
            else:
                if hasattr(self, 'init_button') and self.init_button is not None:
                    self.init_button.setEnabled(True)
                    self.init_button.setText("🤖 重新初始化")
                if error_msg:
                    QMessageBox.critical(self, "错误",
                        f"AI模型初始化失败:\n{error_msg}\n\n请运行: python scripts/simple_model_getter.py")

            self.init_worker = None
        except Exception as e:
            print(f"_on_init_finished error: {e}")
            if hasattr(self, 'init_button') and self.init_button is not None:
                self.init_button.setEnabled(True)
                self.init_button.setText("🤖 重新初始化")

    def _start_face_swap(self):
        """开始换脸处理"""
        if not all([self.source_path, self.target_path, self.output_path]):
            QMessageBox.warning(self, "提示", "请确保已选择所有必要的文件")
            return

        if self.face_swapper is None:
            QMessageBox.warning(self, "提示", "请先初始化AI模型")
            return

        target_face_index = None

        # 检查是否启用多人脸选择
        if self.multi_face_checkbox.isChecked():
            target_ext = Path(self.target_path).suffix.lower()

            if target_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                # 图像文件：显示人脸选择对话框
                try:
                    from gui.face_selector import FaceSelectorDialog
                    dialog = FaceSelectorDialog(self.target_path, self.face_swapper, self)
                    if dialog.exec_() == QDialog.Accepted:
                        target_face_index = dialog.get_selected_index()
                        self._log_message(f"用户选择了人脸索引: {target_face_index}")
                    else:
                        self._log_message("用户取消了人脸选择")
                        return
                except Exception as e:
                    QMessageBox.warning(self, "警告", f"人脸选择失败: {e}\n将使用自动模式")
                    self._log_message(f"人脸选择失败: {e}，使用自动模式", "WARNING")

            elif target_ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv']:
                # 视频文件：使用新的帧选择器 + 多人脸选择
                try:
                    from gui.video_frame_face_selector import VideoFrameFaceSelectorDialog
                    dialog = VideoFrameFaceSelectorDialog(self.target_path, self.face_swapper, self)
                    if dialog.exec_() == QDialog.Accepted:
                        selected_frame_idx = dialog.get_selected_frame_index()
                        selected_face_indices = dialog.get_selected_face_indices()
                        selected_faces_info = dialog.get_selected_faces_info()

                        self._log_message(f"用户选择了第 {selected_frame_idx + 1} 帧的 {len(selected_face_indices)} 个人脸")
                        self._log_message(f"选中的人脸索引: {selected_face_indices}")

                        # 保存选择信息供后续处理使用
                        self.selected_frame_index = selected_frame_idx
                        self.selected_face_indices = selected_face_indices
                        self.selected_faces_info = selected_faces_info

                    else:
                        self._log_message("用户取消了视频人脸选择")
                        return
                except Exception as e:
                    QMessageBox.warning(self, "警告", f"视频人脸选择失败: {e}\n将使用自动模式")
                    self._log_message(f"视频人脸选择失败: {e}，使用自动模式", "WARNING")
            else:
                QMessageBox.information(self, "提示", "不支持的文件格式")
                return

        # 开始处理
        self.is_processing = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        # 记录开始处理的日志
        source_name = Path(self.source_path).name
        target_name = Path(self.target_path).name
        mode_text = f"(选择人脸 #{target_face_index + 1})" if target_face_index is not None else "(自动模式)"
        self._log_message(f"开始换脸处理: {source_name} → {target_name} {mode_text}")

        # 创建工作线程
        selected_face_indices = getattr(self, 'selected_face_indices', None)
        reference_frame_index = getattr(self, 'selected_frame_index', None)

        # 获取背景替换参数
        background_enabled = self.background_checkbox.isChecked()
        background_mode = self._get_background_mode()

        # 检查背景替换设置
        if background_enabled:
            if not self.background_path and not self.background_folder_path:
                QMessageBox.warning(self, "警告", "已启用背景替换但未选择背景图片或文件夹！\n将跳过背景替换。")
                background_enabled = False
            else:
                bg_info = f"模式: {background_mode}"
                if self.background_path:
                    bg_info += f", 背景: {Path(self.background_path).name}"
                elif self.background_folder_path:
                    bg_info += f", 背景文件夹: {Path(self.background_folder_path).name}"
                self._log_message(f"启用背景替换 - {bg_info}", "INFO")

        self.worker = ProcessWorker(
            self.face_swapper,
            self.source_path,
            self.target_path,
            self.output_path,
            target_face_index,
            selected_face_indices,
            reference_frame_index,
            background_enabled,
            background_mode,
            self.background_path,
            self.background_folder_path
        )

        # 连接信号
        self.worker.progress_updated.connect(self._update_progress)
        self.worker.log_message.connect(self._log_message)
        self.worker.finished.connect(self._on_process_finished)
        self.worker.preview_updated.connect(self._update_preview)
        self.worker.model_fallback_occurred.connect(self._on_model_fallback)

        # 开始处理
        self.worker.start()

    def _stop_face_swap(self):
        """停止换脸处理"""
        if self.is_processing and self.worker:
            self._update_status("正在停止处理...")
            self._log_message("用户请求停止处理", "WARNING")

            # 禁用停止按钮，防止重复点击
            self.stop_button.setEnabled(False)

            # 设置停止标志
            self.worker.stop()

            # 不在这里清理GPU内存，让线程自然结束后再清理
            # 温和地等待线程结束
            if self.worker.isRunning():
                # 使用定时器异步等待，避免阻塞主线程
                self._wait_for_worker_finish()
            else:
                # 线程已经结束，直接重置状态
                self._reset_after_stop()

    def _wait_for_worker_finish(self):
        """异步等待工作线程结束"""
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            # 继续等待
            QTimer.singleShot(500, self._wait_for_worker_finish)
        else:
            # 线程已结束，重置状态
            self._reset_after_stop()

    def _reset_after_stop(self):
        """停止后重置状态"""
        try:
            # 轻量级GPU内存清理（不清理分析器）
            self._light_cleanup_gpu_memory()

            # 重置状态
            self.is_processing = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.worker = None

            self._update_status("已停止")
            self._log_message("处理已停止", "INFO")

        except Exception as e:
            self._log_message(f"停止后重置状态失败: {e}", "WARNING")

    def _on_process_finished(self, success):
        """处理完成回调"""
        self.is_processing = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        # 清理GPU内存
        self._cleanup_gpu_memory()

        # 显示完成消息
        self._show_completion_message(success)

        # 重置GPU状态显示
        self._update_gpu_usage_status("待机", "#888888")

    def _cleanup_gpu_memory(self):
        """清理GPU内存（完整版，仅在处理完成时使用）"""
        try:
            # 如果有worker线程，立即清理其GPU内存
            if hasattr(self, 'worker') and self.worker is not None:
                if hasattr(self.worker, 'face_swapper') and self.worker.face_swapper is not None:
                    # 使用立即清理方法
                    self.worker.face_swapper.immediate_gpu_cleanup()

            # 如果主线程有face_swapper，也立即清理其GPU内存
            if hasattr(self, 'face_swapper') and self.face_swapper is not None:
                self.face_swapper.immediate_gpu_cleanup()

            # 强制垃圾回收
            import gc
            for _ in range(3):
                gc.collect()

            self._log_message("GPU内存已彻底清理", "INFO")

        except Exception as e:
            self._log_message(f"GPU内存清理失败: {e}", "WARNING")

    def _light_cleanup_gpu_memory(self):
        """轻量级GPU内存清理（不清理分析器，避免崩溃）"""
        try:
            # 只进行基本的垃圾回收和GPU缓存清理
            import gc
            gc.collect()

            # 如果有torch，清理GPU缓存
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass

            self._log_message("轻量级GPU内存清理完成", "INFO")

        except Exception as e:
            self._log_message(f"轻量级GPU内存清理失败: {e}", "WARNING")

    def closeEvent(self, event):
        """程序关闭事件"""
        try:
            # 停止所有定时器，避免QBasicTimer错误
            if hasattr(self, 'monitor_timer'):
                self.monitor_timer.stop()

            # 如果正在处理，先停止
            if self.is_processing and self.worker:
                self._log_message("程序正在关闭，停止当前处理...", "INFO")
                self.worker.stop()

                # 等待线程结束（最多3秒）
                if self.worker.isRunning():
                    self.worker.wait(3000)

            # 强制清理所有模型（程序退出时安全）
            if hasattr(self, 'worker') and self.worker:
                if hasattr(self.worker, 'face_swapper') and self.worker.face_swapper:
                    self.worker.face_swapper.force_cleanup_models()

            if hasattr(self, 'face_swapper') and self.face_swapper:
                self.face_swapper.force_cleanup_models()

            self._log_message("程序安全退出", "INFO")

        except Exception as e:
            print(f"程序退出清理失败: {e}")

        # 接受关闭事件
        event.accept()

    def _show_completion_message(self, success):
        """显示完成消息"""
        if self.worker and self.worker.stop_requested:
            QMessageBox.information(self, "已停止", "换脸处理已停止")
        elif success:
            QMessageBox.information(self, "成功", f"换脸完成！\n输出文件: {self.output_path}")
        else:
            QMessageBox.critical(self, "失败", "换脸处理失败，请检查输入文件和模型")

        self.worker = None

    def _open_output_folder(self):
        """打开输出文件夹"""
        # 优先使用用户设置的输出路径
        if self.output_path:
            output_dir = Path(self.output_path).parent
        else:
            # 如果没有设置输出路径，使用默认路径
            output_dir = Path("face_swap_results").absolute()

        if output_dir.exists():
            import subprocess
            import platform

            try:
                if platform.system() == "Windows":
                    subprocess.run(["explorer", str(output_dir)])
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", str(output_dir)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(output_dir)])
                self._log_message(f"已打开输出文件夹: {output_dir}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法打开文件夹: {e}")
        else:
            QMessageBox.information(self, "提示", f"输出文件夹不存在: {output_dir}")

    def _show_performance_dialog(self):
        """显示性能优化对话框"""
        if self.face_swapper is None:
            QMessageBox.warning(self, "提示", "请先初始化AI模型")
            return

        try:
            # 获取性能信息
            perf_info = self.face_swapper.get_performance_info()

            # 构建信息文本
            info_text = "🔧 性能信息\n\n"

            # 推理提供者
            info_text += f"推理提供者: {', '.join(perf_info['providers'])}\n"
            info_text += f"GPU加速: {'✅ 启用' if perf_info['gpu_available'] else '❌ 禁用'}\n\n"

            # 模型状态
            info_text += "📊 模型状态\n"
            models = perf_info['models_loaded']
            info_text += f"人脸分析器: {'✅ 已加载' if models['face_analyser'] else '❌ 未加载'}\n"
            info_text += f"换脸模型: {'✅ 已加载' if models['face_swapper'] else '❌ 未加载'}\n\n"

            # 内存使用
            if perf_info['memory_usage']:
                mem = perf_info['memory_usage']
                info_text += f"💾 内存使用\n"
                info_text += f"物理内存: {mem['rss']:.1f} MB\n"
                info_text += f"虚拟内存: {mem['vms']:.1f} MB\n\n"

            # GPU信息
            if perf_info.get('gpu_info'):
                gpu = perf_info['gpu_info']
                info_text += f"🚀 GPU信息\n"
                info_text += f"设备数量: {gpu['device_count']}\n"
                info_text += f"当前设备: {gpu['current_device']}\n"
                info_text += f"已分配内存: {gpu['memory_allocated']:.1f} MB\n"
                info_text += f"保留内存: {gpu['memory_reserved']:.1f} MB\n\n"

            info_text += "🛠️ 优化选项\n"
            info_text += "• 预热模型: 提高后续处理速度\n"
            info_text += "• 清理缓存: 释放内存空间\n"

            # 创建对话框
            dialog = QMessageBox(self)
            dialog.setWindowTitle("性能优化")
            dialog.setText(info_text)
            dialog.setIcon(QMessageBox.Information)

            # 添加自定义按钮
            warm_up_btn = dialog.addButton("🔥 预热模型", QMessageBox.ActionRole)
            clear_cache_btn = dialog.addButton("🧹 清理缓存", QMessageBox.ActionRole)
            dialog.addButton("关闭", QMessageBox.RejectRole)

            # 显示对话框
            dialog.exec_()

            # 处理按钮点击
            clicked_button = dialog.clickedButton()
            if clicked_button == warm_up_btn:
                self._warm_up_models()
            elif clicked_button == clear_cache_btn:
                self._clear_cache()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取性能信息失败:\n{e}")

    def _warm_up_models(self):
        """预热模型"""
        if self.face_swapper is None:
            return

        try:
            self._update_status("正在预热模型...")
            self._log_message("开始预热模型...", "INFO")

            # 在后台线程中预热
            def warm_up_worker():
                try:
                    self.face_swapper.warm_up_models()
                    self._log_message("模型预热完成", "SUCCESS")
                    self._update_status("模型预热完成")
                except Exception as e:
                    self._log_message(f"模型预热失败: {e}", "ERROR")
                    self._update_status("模型预热失败")

            threading.Thread(target=warm_up_worker, daemon=True).start()

        except Exception as e:
            self._log_message(f"预热模型失败: {e}", "ERROR")

    def _clear_cache(self):
        """清理缓存"""
        if self.face_swapper is None:
            return

        try:
            self._update_status("正在清理缓存...")
            self._log_message("开始清理缓存...", "INFO")

            self.face_swapper.clear_cache()

            self._log_message("缓存清理完成", "SUCCESS")
            self._update_status("缓存清理完成")

        except Exception as e:
            self._log_message(f"清理缓存失败: {e}", "ERROR")

    def _on_background_checkbox_changed(self, state):
        """背景替换选项状态改变时的处理"""
        enabled = state == 2  # 选中状态

        # 启用/禁用相关控件
        self.background_mode_combo.setEnabled(enabled)
        self.background_entry.setEnabled(enabled)
        self.bg_select_btn.setEnabled(enabled)

        if enabled:
            self._log_message("已启用背景替换功能", "INFO")
            # 检查当前选择的模型状态
            self._check_background_model_status()
        else:
            self._log_message("已禁用背景替换功能", "INFO")
            # 清空背景路径
            self.background_path = None
            self.background_folder_path = None
            self.background_entry.setText("")
            # 隐藏模型状态和下载按钮
            self.background_status_label.setText("模型状态: 未检查")
            self.download_model_btn.setVisible(False)

    def _on_background_mode_changed(self, mode_text):
        """背景替换模式改变时的处理"""
        if hasattr(self, 'background_checkbox') and self.background_checkbox.isChecked():
            self._check_background_model_status()

    def _check_background_model_status(self):
        """检查背景模型状态"""
        try:
            from core.background_replacer import BackgroundReplacer

            mode = self._get_background_mode()
            replacer = BackgroundReplacer(mode=mode, lazy_init=True)

            # 检查模型可用性
            available, message = replacer.check_model_availability(mode)

            if available:
                self.background_status_label.setText("模型状态: ✅ 已就绪")
                self.background_status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
                self.download_model_btn.setVisible(False)
            else:
                self.background_status_label.setText("模型状态: ❌ 需要下载")
                self.background_status_label.setStyleSheet("color: #F44336; font-size: 12px;")
                self.download_model_btn.setVisible(True)
                self.download_model_btn.setEnabled(True)

        except Exception as e:
            self.background_status_label.setText(f"模型状态: ❌ 检查失败")
            self.background_status_label.setStyleSheet("color: #F44336; font-size: 12px;")
            self._log_message(f"检查背景模型状态失败: {e}", "ERROR")

    def _handle_background_model_fallback(self, status):
        """处理背景模型回退状态"""
        if status['fallback_occurred']:
            # 更新下拉菜单到实际使用的模式
            self._update_background_mode_combo(status['current_mode'])

            # 显示回退状态
            original_display = self._get_mode_display_name(status['original_mode'])
            current_display = self._get_mode_display_name(status['current_mode'])

            self.background_status_label.setText(f"模型状态: ⚠️ 已回退")
            self.background_status_label.setStyleSheet("color: #FF9800; font-size: 12px;")
            self.download_model_btn.setVisible(False)

            # 记录详细的回退信息
            self._log_message(f"背景模型回退: {original_display} → {current_display}", "WARNING")
            if status.get('fallback_reason'):
                self._log_message(f"回退原因: {status['fallback_reason']}", "WARNING")

            return True
        return False

    def _download_background_model(self):
        """下载背景模型"""
        try:
            from core.background_replacer import BackgroundReplacer
            from PyQt5.QtCore import QThread, pyqtSignal

            mode = self._get_background_mode()

            # 创建下载线程
            class ModelDownloadThread(QThread):
                progress_updated = pyqtSignal(int, int, str)
                download_finished = pyqtSignal(bool, str)

                def __init__(self, mode):
                    super().__init__()
                    self.mode = mode

                def run(self):
                    try:
                        replacer = BackgroundReplacer(mode=self.mode, lazy_init=True)

                        def progress_callback(current, total, message):
                            self.progress_updated.emit(current, total, message)

                        replacer.initialize_async(progress_callback)

                        if replacer.is_available():
                            status = replacer.get_model_status()
                            if status['fallback_occurred']:
                                self.download_finished.emit(True, f"模型下载完成，但回退到了 {status['current_mode']} 模式")
                            else:
                                self.download_finished.emit(True, "模型下载完成")
                        else:
                            error = replacer.get_initialization_error()
                            self.download_finished.emit(False, f"模型下载失败: {error}")

                    except Exception as e:
                        self.download_finished.emit(False, f"下载过程中出错: {e}")

            # 禁用下载按钮，显示下载状态
            self.download_model_btn.setEnabled(False)
            self.download_model_btn.setText("下载中...")
            self.background_status_label.setText("模型状态: 🔄 下载中...")
            self.background_status_label.setStyleSheet("color: #2196F3; font-size: 12px;")

            # 启动下载线程
            self.download_thread = ModelDownloadThread(mode)
            self.download_thread.progress_updated.connect(self._on_download_progress)
            self.download_thread.download_finished.connect(self._on_download_finished)
            self.download_thread.start()

        except Exception as e:
            self._log_message(f"启动模型下载失败: {e}", "ERROR")
            self.download_model_btn.setEnabled(True)
            self.download_model_btn.setText("下载模型")

    def _on_download_progress(self, current, total, message):
        """下载进度更新"""
        progress = int((current / total) * 100) if total > 0 else 0
        self.background_status_label.setText(f"模型状态: 🔄 下载中... {progress}%")
        self._log_message(f"模型下载进度: {message} ({current}/{total})", "INFO")

    def _on_download_finished(self, success, message):
        """下载完成"""
        if success:
            # 检查是否发生了回退
            try:
                from core.background_replacer import BackgroundReplacer
                mode = self._get_background_mode()
                replacer = BackgroundReplacer(mode=mode, lazy_init=True)
                status = replacer.get_model_status()

                # 处理回退状态
                if not self._handle_background_model_fallback(status):
                    # 没有回退，正常完成
                    self.background_status_label.setText("模型状态: ✅ 已就绪")
                    self.background_status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
                    self.download_model_btn.setVisible(False)
                    self._log_message(f"背景模型下载成功: {message}", "SUCCESS")

            except Exception as e:
                # 如果检查状态失败，仍然显示成功
                self.background_status_label.setText("模型状态: ✅ 已就绪")
                self.background_status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
                self.download_model_btn.setVisible(False)
                self._log_message(f"背景模型下载成功: {message}", "SUCCESS")
                self._log_message(f"状态检查失败: {e}", "WARNING")
        else:
            self.background_status_label.setText("模型状态: ❌ 下载失败")
            self.background_status_label.setStyleSheet("color: #F44336; font-size: 12px;")
            self.download_model_btn.setEnabled(True)
            self.download_model_btn.setText("重试下载")
            self._log_message(f"背景模型下载失败: {message}", "ERROR")

        # 清理下载线程
        if hasattr(self, 'download_thread'):
            self.download_thread.deleteLater()
            delattr(self, 'download_thread')

    def _on_model_fallback(self, status):
        """处理模型回退信号"""
        try:
            # 处理回退状态
            self._handle_background_model_fallback(status)
        except Exception as e:
            self._log_message(f"处理模型回退状态失败: {e}", "ERROR")

    def _select_background(self):
        """统一的背景选择方法，支持文件和文件夹"""
        from PyQt5.QtWidgets import QMessageBox

        # 创建选择对话框
        reply = QMessageBox.question(
            self, "选择背景类型",
            "请选择背景类型：\n\n• 是：选择单张图片（固定背景）\n• 否：选择文件夹（随机背景）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 选择单张图片
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择背景图片", "",
                "图像文件 (*.jpg *.jpeg *.png *.bmp *.tiff);;所有文件 (*.*)"
            )
            if file_path:
                self.background_path = file_path
                self.background_folder_path = None  # 清空文件夹路径
                self.background_entry.setText(file_path)
                self._log_message(f"已选择背景图片: {Path(file_path).name}", "INFO")

        elif reply == QMessageBox.StandardButton.No:
            # 选择文件夹
            folder_path = QFileDialog.getExistingDirectory(self, "选择背景文件夹")
            if folder_path:
                # 检查文件夹中是否有图片文件
                image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
                image_files = []

                for file_path in Path(folder_path).iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                        image_files.append(file_path)

                if image_files:
                    self.background_folder_path = folder_path
                    self.background_path = None  # 清空单个图片路径
                    self.background_entry.setText(f"{folder_path} ({len(image_files)}张图片)")
                    self._log_message(f"已选择背景文件夹: {Path(folder_path).name} (包含{len(image_files)}张图片)", "INFO")
                else:
                    QMessageBox.warning(self, "警告", "选择的文件夹中没有找到图片文件！")

    def _get_background_mode(self):
        """获取当前选择的背景替换模式"""
        mode_text = self.background_mode_combo.currentText()
        if "BackgroundMattingV2" in mode_text:
            return "backgroundmattingv2"
        elif "MODNet" in mode_text:
            return "modnet"
        elif "U2Net" in mode_text:
            return "u2net"
        elif "Rembg" in mode_text:
            return "rembg"
        else:
            return "backgroundmattingv2"  # 默认

    def _get_mode_display_name(self, mode):
        """获取模式的显示名称"""
        mode_map = {
            'backgroundmattingv2': "BackgroundMattingV2 (推荐)",
            'modnet': "MODNet (快速)",
            'u2net': "U2Net (通用)",
            'rembg': "Rembg (简单)"
        }
        return mode_map.get(mode.lower(), mode)

    def _update_background_mode_combo(self, actual_mode):
        """更新背景模式下拉菜单到实际使用的模式"""
        display_name = self._get_mode_display_name(actual_mode)

        # 查找对应的索引
        for i in range(self.background_mode_combo.count()):
            if display_name in self.background_mode_combo.itemText(i):
                # 临时断开信号连接，避免触发检查
                self.background_mode_combo.currentTextChanged.disconnect()
                self.background_mode_combo.setCurrentIndex(i)
                # 重新连接信号
                self.background_mode_combo.currentTextChanged.connect(self._on_background_mode_changed)
                break

    def _get_random_background(self):
        """从背景文件夹中随机选择一张背景图片"""
        if not self.background_folder_path:
            return None

        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        image_files = []

        for file_path in Path(self.background_folder_path).iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                image_files.append(file_path)

        if image_files:
            import random
            return str(random.choice(image_files))
        return None

def main(gpu_config=None):
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用信息
    app.setApplicationName("AI换脸【秘灵】")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("AI换脸【秘灵】")

    # 创建主窗口，传递GPU配置
    window = ModernFaceSwapGUI(gpu_config=gpu_config)
    window.show()

    # 运行应用
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
