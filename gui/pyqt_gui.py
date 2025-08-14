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
    QGroupBox, QGridLayout, QSpacerItem, QSizePolicy, QDialog
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

    def __init__(self, face_swapper, source_path, target_path, output_path, target_face_index=None, reference_face_path=None, selected_face_indices=None, reference_frame_index=None):
        super().__init__()
        self.face_swapper = face_swapper
        self.source_path = source_path
        self.target_path = target_path
        self.output_path = output_path
        self.target_face_index = target_face_index  # 目标人脸索引，None表示自动选择（旧版兼容）
        self.reference_face_path = reference_face_path  # 参考人脸路径，用于跟踪
        self.selected_face_indices = selected_face_indices  # 选中的人脸索引列表（新版多人脸选择）
        self.reference_frame_index = reference_frame_index  # 参考帧索引（新版多人脸选择）
        self.stop_requested = False
    
    def stop(self):
        """停止处理"""
        self.stop_requested = True
    
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
                        frame_info = f"帧 {current_frame}/{total_frames}"
                        if extra_msg:
                            frame_info += f" - {extra_msg}"
                        self.preview_updated.emit(original_frame, result_frame, frame_info)

                    return True

                success = self.face_swapper.process_video(
                    self.source_path,
                    self.target_path,
                    self.output_path,
                    progress_callback=progress_callback,
                    stop_callback=lambda: self.stop_requested,
                    target_face_index=self.target_face_index,
                    reference_face_path=self.reference_face_path,
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
    
    def __init__(self):
        super().__init__()
        
        # 初始化变量
        self.face_swapper = None
        self.source_path = None
        self.target_path = None
        self.output_path = None
        self.reference_path = None  # 参考人脸路径
        self.is_processing = False
        self.worker = None
        
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
                border: 2px solid #007acc;
                border-radius: 3px;
                background-color: #007acc;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
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
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel("🎭 AI换脸【秘灵】")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setStyleSheet("color: #333333; margin: 10px;")
        main_layout.addWidget(title_label)

        # 创建主水平分割器：左侧所有功能 | 右侧预览
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)

        # 左侧：所有功能区域的垂直布局
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(15)

        # 文件选择区域
        self._create_file_section(left_layout)

        # 控制面板
        self._create_control_section(left_layout)

        # 日志和状态区域
        log_panel = self._create_log_status_panel()
        left_layout.addWidget(log_panel)

        main_splitter.addWidget(left_panel)

        # 右侧：预览区域（占据整个右侧高度）
        preview_panel = self._create_preview_panel()
        main_splitter.addWidget(preview_panel)

        # 设置分割比例 (左侧功能:右侧预览 = 3:2)
        main_splitter.setSizes([960, 640])

    def _create_file_section(self, parent_layout):
        """创建文件选择区域"""
        file_group = QGroupBox("📁 文件选择")
        parent_layout.addWidget(file_group)

        layout = QGridLayout(file_group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        # 源人脸选择
        source_label = QLabel("源人脸图像:")
        source_label.setFont(QFont("Arial", 12))
        layout.addWidget(source_label, 0, 0)
        self.source_entry = QLineEdit()
        self.source_entry.setPlaceholderText("选择源人脸图像文件...")
        layout.addWidget(self.source_entry, 0, 1)

        source_btn = QPushButton("浏览")
        source_btn.clicked.connect(self._select_source_file)
        layout.addWidget(source_btn, 0, 2)

        # 目标文件选择
        target_label = QLabel("目标图像/视频:")
        target_label.setFont(QFont("Arial", 12))
        layout.addWidget(target_label, 1, 0)
        self.target_entry = QLineEdit()
        self.target_entry.setPlaceholderText("选择目标图像或视频文件...")
        layout.addWidget(self.target_entry, 1, 1)

        target_btn = QPushButton("浏览")
        target_btn.clicked.connect(self._select_target_file)
        layout.addWidget(target_btn, 1, 2)

        # 输出路径
        output_label = QLabel("输出路径:")
        output_label.setFont(QFont("Arial", 12))
        layout.addWidget(output_label, 2, 0)
        self.output_entry = QLineEdit()
        self.output_entry.setPlaceholderText("自动生成输出路径...")
        layout.addWidget(self.output_entry, 2, 1)

        output_btn = QPushButton("选择")
        output_btn.clicked.connect(self._select_output_file)
        layout.addWidget(output_btn, 2, 2)

        # 参考人脸（用于跟踪）
        self.reference_label = QLabel("参考人脸（跟踪用）:")
        self.reference_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.reference_label, 3, 0)

        self.reference_entry = QLineEdit()
        self.reference_entry.setPlaceholderText("选择要跟踪的参考人脸图像...")
        layout.addWidget(self.reference_entry, 3, 1)

        self.reference_btn = QPushButton("浏览")
        self.reference_btn.clicked.connect(self._select_reference_file)
        layout.addWidget(self.reference_btn, 3, 2)

        # 初始时隐藏参考人脸选择
        self.reference_label.setVisible(False)
        self.reference_entry.setVisible(False)
        self.reference_btn.setVisible(False)

        # 设置列宽比例
        layout.setColumnStretch(1, 1)

    def _create_control_section(self, parent_layout):
        """创建控制面板"""
        control_group = QGroupBox("🎛️ 控制面板")
        parent_layout.addWidget(control_group)

        # 使用垂直布局来创建两行
        main_layout = QVBoxLayout(control_group)
        main_layout.setContentsMargins(20, 25, 20, 20)
        main_layout.setSpacing(10)

        # 第一行：主要操作按钮
        first_row = QHBoxLayout()

        # 初始化AI按钮
        self.init_button = QPushButton("🤖 初始化AI")
        self.init_button.clicked.connect(self._manual_init_ai)
        first_row.addWidget(self.init_button)

        # 开始按钮
        self.start_button = QPushButton("🚀 开始换脸")
        self.start_button.clicked.connect(self._start_face_swap)
        self.start_button.setEnabled(False)
        first_row.addWidget(self.start_button)

        # 停止按钮
        self.stop_button = QPushButton("⏹ 停止")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.clicked.connect(self._stop_face_swap)
        self.stop_button.setEnabled(False)
        first_row.addWidget(self.stop_button)

        # 打开文件夹按钮
        folder_btn = QPushButton("📁 打开输出文件夹")
        folder_btn.clicked.connect(self._open_output_folder)
        first_row.addWidget(folder_btn)

        main_layout.addLayout(first_row)

        # 第二行：选项和设置
        second_row = QHBoxLayout()

        # GPU选项
        self.gpu_checkbox = QCheckBox("🚀 GPU加速")
        self.gpu_checkbox.setChecked(True)
        second_row.addWidget(self.gpu_checkbox)

        # 多人脸选择选项
        self.multi_face_checkbox = QCheckBox("🎯 多人脸选择")
        self.multi_face_checkbox.setChecked(False)
        second_row.addWidget(self.multi_face_checkbox)

        # 人脸跟踪选项
        self.face_tracking_checkbox = QCheckBox("🔍 人脸跟踪")
        self.face_tracking_checkbox.setChecked(False)
        self.face_tracking_checkbox.setToolTip("⚠️ 重要：参考人脸必须是视频中的同一个人\n匹配度说明：70-100%=同一人，40-69%=相似，<40%=不同人")
        self.face_tracking_checkbox.toggled.connect(self._on_face_tracking_toggled)
        second_row.addWidget(self.face_tracking_checkbox)

        # 性能优化按钮 - 添加详细说明
        perf_btn = QPushButton("⚡ 性能优化")
        perf_btn.setToolTip("🔧 性能优化设置：\n• 调整处理线程数\n• 设置内存使用限制\n• 优化GPU显存分配\n• 配置批处理大小\n• 启用/禁用特定优化算法")
        perf_btn.clicked.connect(self._show_performance_dialog)
        second_row.addWidget(perf_btn)

        # 添加弹性空间，让控件左对齐
        second_row.addStretch()

        main_layout.addLayout(second_row)

    def _create_log_status_panel(self):
        """创建日志和状态面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        # 日志区域
        log_group = QGroupBox("📋 执行日志")
        layout.addWidget(log_group)

        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(20, 25, 20, 20)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)

        # 初始日志
        self._log_message("=== AI换脸应用程序日志 ===", "INFO")
        self._log_message("点击'🤖 初始化AI'开始使用", "INFO")

        # 状态栏
        status_group = QGroupBox("📊 状态")
        layout.addWidget(status_group)

        status_layout = QHBoxLayout(status_group)
        status_layout.setContentsMargins(20, 25, 20, 20)

        self.status_label = QLabel("就绪")
        self.status_label.setFont(QFont("Arial", 16))
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumWidth(300)
        self.progress_bar.setValue(0)
        status_layout.addWidget(self.progress_bar)

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

        # 添加到日志框
        self.log_text.insertHtml(log_line)
        self.log_text.ensureCursorVisible()

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

    def _select_reference_file(self):
        """选择参考人脸文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择参考人脸图像",
            "",
            "图像文件 (*.jpg *.jpeg *.png *.bmp *.tiff);;所有文件 (*.*)"
        )

        if file_path:
            self.reference_path = file_path
            self.reference_entry.setText(file_path)
            self._update_status(f"已选择参考人脸: {Path(file_path).name}")
            self._log_message(f"已选择参考人脸图像: {Path(file_path).name}")
            self._check_ready_to_start()

    def _on_face_tracking_toggled(self, checked):
        """人脸跟踪选项切换"""
        # 显示或隐藏参考人脸选择
        self.reference_label.setVisible(checked)
        self.reference_entry.setVisible(checked)
        self.reference_btn.setVisible(checked)

        if checked:
            self._log_message("启用人脸跟踪模式，请选择参考人脸图像")
            self._log_message("⚠️ 重要提示：参考人脸必须是视频中的同一个人，否则匹配度会很低", "WARNING")
            # 禁用多人脸选择（两种模式互斥）
            self.multi_face_checkbox.setChecked(False)
        else:
            self.reference_path = None
            self.reference_entry.clear()
            self._log_message("禁用人脸跟踪模式")

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

            # 检查人脸跟踪模式的额外条件
            has_reference = True  # 默认不需要参考人脸
            if self.face_tracking_checkbox.isChecked():
                has_reference = bool(self.reference_path) and Path(str(self.reference_path)).exists() if self.reference_path else False

            # 确保ready是布尔值
            ready = bool(has_source and has_target and has_output and has_swapper and has_reference)

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
                elif not has_reference:
                    self._update_status("请选择参考人脸图像")

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
                    self.log_message.emit(f"GPU加速: {'启用' if self.use_gpu else '禁用'}", "INFO")

                    self.face_swapper = FaceSwapper(use_gpu=self.use_gpu)

                    self.status_updated.emit("AI模型初始化完成，就绪")
                    self.log_message.emit("AI模型初始化完成", "SUCCESS")
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
        reference_face_path = None

        # 检查是否启用人脸跟踪模式
        if self.face_tracking_checkbox.isChecked():
            if self.reference_path:
                reference_face_path = self.reference_path
                self._log_message(f"使用人脸跟踪模式，参考人脸: {Path(reference_face_path).name}")
            else:
                QMessageBox.warning(self, "提示", "请先选择参考人脸图像")
                return

        # 检查是否启用多人脸选择
        elif self.multi_face_checkbox.isChecked():
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

        self.worker = ProcessWorker(
            self.face_swapper,
            self.source_path,
            self.target_path,
            self.output_path,
            target_face_index,
            reference_face_path,
            selected_face_indices,
            reference_frame_index
        )

        # 连接信号
        self.worker.progress_updated.connect(self._update_progress)
        self.worker.log_message.connect(self._log_message)
        self.worker.finished.connect(self._on_process_finished)
        self.worker.preview_updated.connect(self._update_preview)

        # 开始处理
        self.worker.start()

    def _stop_face_swap(self):
        """停止换脸处理"""
        if self.is_processing and self.worker:
            self.worker.stop()
            self._update_status("正在停止处理...")
            self._log_message("用户请求停止处理", "WARNING")

            # 禁用停止按钮，防止重复点击
            self.stop_button.setEnabled(False)

            # 温和地等待线程结束，不使用强制终止
            if self.worker.isRunning():
                self.worker.wait(5000)  # 等待5秒让线程自然结束

            # 重置状态
            self.is_processing = False
            self.start_button.setEnabled(True)
            self.worker = None

    def _on_process_finished(self, success):
        """处理完成回调"""
        self.is_processing = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

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

def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用信息
    app.setApplicationName("AI换脸【秘灵】")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("AI换脸【秘灵】")

    # 创建主窗口
    window = ModernFaceSwapGUI()
    window.show()

    # 运行应用
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
