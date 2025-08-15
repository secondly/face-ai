"""
视频帧选择器 + 多人脸选择对话框
支持用户选择任意帧，然后从该帧中选择多个人脸进行替换
"""

import cv2
import numpy as np
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import logging

logger = logging.getLogger(__name__)


class VirtualFrameScrollWidget(QWidget):
    """虚拟滚动帧组件，提升大量帧的显示性能"""

    def __init__(self, frame_thumbnails, click_callback, parent=None):
        super().__init__(parent)
        self.frame_thumbnails = frame_thumbnails
        self.click_callback = click_callback
        self.visible_widgets = []
        self.selected_index = -1

        # 每个缩略图的尺寸
        self.item_width = 125  # 120 + 5 spacing
        self.item_height = 85  # 80 + 5 spacing

        # 可见区域参数
        self.visible_start = 0
        self.visible_count = 10  # 初始值，会根据容器宽度动态调整

        # 设置大小策略为可扩展
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._setup_ui()
        # 延迟更新，等待布局完成
        QTimer.singleShot(0, self._delayed_update)

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 滚动条
        self.scroll_bar = QScrollBar(Qt.Horizontal)
        self.scroll_bar.setMinimum(0)
        self.scroll_bar.setMaximum(max(0, len(self.frame_thumbnails) - self.visible_count))
        self.scroll_bar.valueChanged.connect(self._on_scroll)
        layout.addWidget(self.scroll_bar)

        # 帧显示区域
        self.frame_area = QWidget()
        self.frame_area.setFixedHeight(self.item_height)
        self.frame_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.frame_layout = QHBoxLayout(self.frame_area)
        self.frame_layout.setSpacing(5)
        self.frame_layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.frame_area)

        # 不设置固定宽度，让组件自适应父容器

    def _on_scroll(self, value):
        """滚动事件"""
        self.visible_start = value
        self._update_visible_items()

    def _calculate_visible_count(self):
        """根据容器宽度计算可见帧数量"""
        container_width = self.width()
        if container_width <= 0:
            return 10  # 默认值

        # 减去边距和滚动条空间
        available_width = container_width - 20  # 左右边距
        frames_count = max(1, available_width // self.item_width)

        # 限制最大显示数量，避免性能问题
        return min(frames_count, len(self.frame_thumbnails))

    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 重新计算可见帧数量
        old_count = self.visible_count
        self.visible_count = self._calculate_visible_count()

        # 更新滚动条范围
        self.scroll_bar.setMaximum(max(0, len(self.frame_thumbnails) - self.visible_count))

        # 如果可见数量发生变化，更新显示
        if old_count != self.visible_count:
            self._update_visible_items()

    def _delayed_update(self):
        """延迟更新，等待布局完成后计算正确的宽度"""
        self.visible_count = self._calculate_visible_count()
        self.scroll_bar.setMaximum(max(0, len(self.frame_thumbnails) - self.visible_count))
        self._update_visible_items()

    def _update_visible_items(self):
        """更新可见的帧组件 - 优化性能，复用组件"""
        end_index = min(self.visible_start + self.visible_count, len(self.frame_thumbnails))
        needed_count = end_index - self.visible_start

        # 复用现有组件，只在必要时创建新组件
        while len(self.visible_widgets) < needed_count:
            # 创建一个空的占位组件，稍后会更新内容
            frame_widget = FrameThumbnailWidget(0, self.frame_thumbnails[0] if self.frame_thumbnails else None)
            frame_widget.clicked.connect(self.click_callback)
            self.visible_widgets.append(frame_widget)
            self.frame_layout.addWidget(frame_widget)

        # 隐藏多余的组件
        for i in range(needed_count, len(self.visible_widgets)):
            self.visible_widgets[i].hide()

        # 更新可见组件的内容
        for i in range(needed_count):
            frame_index = self.visible_start + i
            thumbnail = self.frame_thumbnails[frame_index]
            widget = self.visible_widgets[i]

            # 只在内容发生变化时才更新显示
            if widget.frame_index != frame_index or widget.frame_image is not thumbnail:
                widget.frame_index = frame_index
                widget.frame_image = thumbnail
                widget._update_display()

            widget.set_selected(frame_index == self.selected_index)
            widget.show()

        # 移除弹性空间（如果存在）
        if hasattr(self, '_stretch_item'):
            self.frame_layout.removeItem(self._stretch_item)

        # 添加弹性空间
        self._stretch_item = self.frame_layout.addStretch()

    def set_selected_frame(self, frame_index):
        """设置选中的帧"""
        # 取消之前的选择
        for widget in self.visible_widgets:
            widget.set_selected(False)

        self.selected_index = frame_index

        # 如果选中的帧不在可见范围内，滚动到该位置
        if frame_index < self.visible_start or frame_index >= self.visible_start + self.visible_count:
            # 将选中的帧居中显示
            new_start = max(0, frame_index - self.visible_count // 2)
            new_start = min(new_start, len(self.frame_thumbnails) - self.visible_count)
            self.scroll_bar.setValue(new_start)

        # 更新选中状态
        for widget in self.visible_widgets:
            if hasattr(widget, 'frame_index') and widget.frame_index == frame_index:
                widget.set_selected(True)


class FrameThumbnailWidget(QLabel):
    """帧缩略图组件"""
    clicked = pyqtSignal(int)  # 发送帧索引
    
    def __init__(self, frame_index, frame_image, parent=None):
        super().__init__(parent)
        self.frame_index = frame_index
        self.frame_image = frame_image
        self.is_selected = False
        
        # 设置固定大小
        self.setFixedSize(120, 80)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QLabel:hover {
                border-color: #007acc;
            }
        """)
        
        # 显示缩略图
        self._update_thumbnail()
        
    def _update_thumbnail(self):
        """更新缩略图显示"""
        if self.frame_image is None:
            return

        # 转换为QPixmap
        height, width, channel = self.frame_image.shape
        bytes_per_line = 3 * width
        q_image = QImage(self.frame_image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_image)

        # 缩放到合适大小
        scaled_pixmap = pixmap.scaled(116, 76, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(scaled_pixmap)

    def _update_display(self):
        """更新显示内容 - 用于虚拟滚动性能优化"""
        self._update_thumbnail()
        
    def set_selected(self, selected):
        """设置选中状态"""
        self.is_selected = selected
        if selected:
            self.setStyleSheet("""
                QLabel {
                    border: 3px solid #007acc;
                    border-radius: 4px;
                    background-color: #f0f8ff;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel {
                    border: 2px solid #ddd;
                    border-radius: 4px;
                    background-color: white;
                }
                QLabel:hover {
                    border-color: #007acc;
                }
            """)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.frame_index)


class FaceCheckboxWidget(QWidget):
    """人脸选择复选框组件"""
    
    def __init__(self, face_info, face_preview, face_index, parent=None):
        super().__init__(parent)
        self.face_info = face_info
        self.face_preview = face_preview
        self.face_index = face_index
        
        self._setup_ui()
        
    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # 复选框
        self.checkbox = QCheckBox(f"人脸 #{self.face_index + 1}")
        self.checkbox.setFont(QFont("Arial", 10, QFont.Bold))
        self.checkbox.toggled.connect(self._on_checkbox_toggled)
        layout.addWidget(self.checkbox)
        
        # 人脸预览图
        self.image_label = QLabel()
        self.image_label.setFixedSize(150, 150)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)
        
        # 显示人脸预览 - 保持原色，不进行颜色通道转换
        if self.face_preview is not None:
            height, width, channel = self.face_preview.shape
            bytes_per_line = 3 * width
            # 移除 rgbSwapped() 以保持原始颜色
            q_image = QImage(self.face_preview.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(146, 146, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        
        layout.addWidget(self.image_label)
        
        # 人脸信息
        info_text = f"大小: {self.face_info['area']} 像素\n"
        info_text += f"位置: ({self.face_info['center'][0]}, {self.face_info['center'][1]})\n"
        info_text += f"置信度: {self.face_info['confidence']:.2f}"
        
        self.info_label = QLabel(info_text)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setFont(QFont("Arial", 9))
        self.info_label.setStyleSheet("color: #666;")
        layout.addWidget(self.info_label)
        
        # 设置整体样式
        self.setStyleSheet("""
            QWidget {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: white;
            }
            QWidget:hover {
                border-color: #007acc;
                background-color: #f8f9fa;
            }
        """)
    
    def is_checked(self):
        """是否被选中"""
        return self.checkbox.isChecked()
    
    def set_checked(self, checked):
        """设置选中状态"""
        self.checkbox.setChecked(checked)

    def _on_checkbox_toggled(self, checked):
        """复选框状态改变"""
        # 通知父对话框更新确认按钮状态
        parent_dialog = self.parent()
        while parent_dialog and not isinstance(parent_dialog, VideoFrameFaceSelectorDialog):
            parent_dialog = parent_dialog.parent()

        if parent_dialog:
            parent_dialog._update_confirm_button()


class VideoFrameFaceSelectorDialog(QDialog):
    """视频帧选择器 + 多人脸选择对话框"""
    
    def __init__(self, video_path, face_swapper=None, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.face_swapper = face_swapper
        self.selected_frame_index = 0
        self.selected_face_indices = []
        
        self.frames = []
        self.frame_thumbnails = []
        self.face_widgets = []
        self.current_faces = []

        # 加载进度对话框
        self.loading_dialog = None
        self.loading_label = None
        
        self.setWindowTitle("选择视频帧和人脸")
        self.setModal(True)
        # 设置与主界面相同的宽度
        self.resize(1400, 800)
        self.setMinimumSize(1000, 700)  # 与主界面保持一致
        
        self._load_video_frames()
        self._setup_ui()
        
        # 默认选择第一帧
        if self.frames:
            QTimer.singleShot(100, lambda: self._on_frame_selected(0))
    
    def _load_video_frames(self):
        """加载视频帧（超过200帧时随机抽取100帧）"""
        try:
            cap = cv2.VideoCapture(str(self.video_path))
            if not cap.isOpened():
                raise ValueError("无法打开视频文件")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            # 根据总帧数决定采样策略
            if total_frames > 200:
                # 随机抽取100帧
                import random
                frame_indices = sorted(random.sample(range(total_frames), min(100, total_frames)))
                logger.info(f"视频总帧数: {total_frames}, 随机抽取 {len(frame_indices)} 帧")
            else:
                # 加载所有帧
                frame_indices = list(range(total_frames))
                logger.info(f"视频总帧数: {total_frames}, 将加载所有帧")

            # 保存原始总帧数和当前帧索引，用于重新随机
            self.total_frames = total_frames
            self.current_frame_indices = frame_indices

            # 创建加载进度对话框（显示实际要加载的帧数）
            self._show_loading_dialog(len(frame_indices))

            # 读取选中的帧（只保存缩略图，节省内存）
            for i, frame_idx in enumerate(frame_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    # 只保存帧索引，不保存完整帧（节省内存）
                    self.frames.append((frame_idx, None))

                    # 创建缩略图
                    thumbnail = cv2.resize(frame, (120, 80))
                    self.frame_thumbnails.append(thumbnail)

                # 更新进度（显示实际进度）
                self._update_loading_progress(i + 1, len(frame_indices))

                # 处理事件，保持界面响应
                QApplication.processEvents()

            cap.release()

            # 关闭加载对话框
            self._hide_loading_dialog()

            logger.info(f"视频帧加载完成，共 {len(self.frames)} 帧")

        except Exception as e:
            # 确保关闭加载对话框
            self._hide_loading_dialog()
            QMessageBox.critical(self, "错误", f"视频加载失败:\n{e}")
            self.reject()

    def _reload_random_frames(self):
        """重新随机抽取100帧"""
        if not hasattr(self, 'total_frames') or self.total_frames <= 200:
            QMessageBox.information(self, "提示", "当前视频帧数不超过200帧，无需重新随机抽取")
            return

        try:
            # 清空当前数据
            self.frames.clear()
            self.frame_thumbnails.clear()

            # 重新随机抽取
            import random
            frame_indices = sorted(random.sample(range(self.total_frames), min(100, self.total_frames)))
            self.current_frame_indices = frame_indices

            logger.info(f"重新随机抽取 {len(frame_indices)} 帧")

            # 重新加载帧
            cap = cv2.VideoCapture(str(self.video_path))
            if not cap.isOpened():
                raise ValueError("无法打开视频文件")

            # 显示加载进度
            self._show_loading_dialog(len(frame_indices))

            # 读取选中的帧
            for i, frame_idx in enumerate(frame_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()

                if ret:
                    # 保存帧索引（与初始加载保持一致）
                    self.frames.append((frame_idx, None))

                    # 创建缩略图
                    thumbnail = cv2.resize(frame, (120, 80))
                    self.frame_thumbnails.append(thumbnail)

                # 更新进度
                self._update_loading_progress(i + 1, len(frame_indices))
                QApplication.processEvents()

            cap.release()
            self._hide_loading_dialog()

            # 刷新界面
            self._refresh_frame_display()

            # 默认选择第一帧
            if self.frames:
                QTimer.singleShot(100, lambda: self._on_frame_selected(0))

            logger.info(f"重新随机抽取完成，共 {len(self.frames)} 帧")

        except Exception as e:
            self._hide_loading_dialog()
            QMessageBox.critical(self, "错误", f"重新随机抽取失败:\n{e}")

    def _refresh_frame_display(self):
        """刷新帧显示"""
        if hasattr(self, 'frame_scroll_widget'):
            # 更新虚拟滚动组件的数据
            self.frame_scroll_widget.frame_thumbnails = self.frame_thumbnails
            self.frame_scroll_widget.selected_index = -1
            # 更新滚动条范围
            self.frame_scroll_widget.scroll_bar.setMaximum(max(0, len(self.frame_thumbnails) - self.frame_scroll_widget.visible_count))
            # 重置滚动位置
            self.frame_scroll_widget.visible_start = 0
            self.frame_scroll_widget.scroll_bar.setValue(0)
            # 更新显示
            self.frame_scroll_widget._update_visible_items()

        # 更新帧信息标签
        if hasattr(self, 'frame_info_label'):
            frame_count_text = f"视频共 {getattr(self, 'total_frames', len(self.frames))} 帧"
            if hasattr(self, 'total_frames') and self.total_frames > 200:
                frame_count_text += f"，当前显示随机抽取的 {len(self.frames)} 帧"
            else:
                frame_count_text += f"，显示所有 {len(self.frames)} 帧"
            self.frame_info_label.setText(frame_count_text + "，请拖动滚动条选择任意一帧")

        # 清除当前人脸选择
        self._clear_face_widgets()

    def _show_loading_dialog(self, total_frames):
        """显示加载进度对话框"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
        from PyQt5.QtCore import Qt

        self.loading_dialog = QDialog(self)
        self.loading_dialog.setWindowTitle("加载视频帧")
        self.loading_dialog.setModal(True)
        self.loading_dialog.setFixedSize(400, 120)
        self.loading_dialog.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        layout = QVBoxLayout(self.loading_dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题 - 根据是否随机抽取显示不同文本
        if hasattr(self, 'total_frames') and self.total_frames > 200:
            title_text = f"正在随机抽取 {total_frames} 帧，请稍候..."
        else:
            title_text = "正在读取视频帧，请稍候..."

        title_label = QLabel(title_text)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        layout.addWidget(title_label)

        # 进度信息
        self.loading_label = QLabel(f"当前已读取 0/{total_frames} 帧")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.loading_label)

        # 进度条
        self.loading_progress = QProgressBar()
        self.loading_progress.setRange(0, total_frames)
        self.loading_progress.setValue(0)
        self.loading_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.loading_progress)

        # 显示对话框
        self.loading_dialog.show()
        QApplication.processEvents()

    def _update_loading_progress(self, current, total):
        """更新加载进度"""
        if self.loading_dialog and self.loading_label:
            self.loading_label.setText(f"当前已读取 {current}/{total} 帧")
            self.loading_progress.setValue(current)
            QApplication.processEvents()

    def _hide_loading_dialog(self):
        """隐藏加载进度对话框"""
        if self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None
            self.loading_label = None
    
    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("🎬 选择视频帧和要替换的人脸")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # 上半部分：帧选择器
        frame_widget = self._create_frame_selector()
        splitter.addWidget(frame_widget)
        
        # 下半部分：人脸选择器
        self.face_widget = self._create_face_selector()
        splitter.addWidget(self.face_widget)
        
        # 设置分割比例
        splitter.setStretchFactor(0, 1)  # 帧选择器占1/3
        splitter.setStretchFactor(1, 2)  # 人脸选择器占2/3
        
        # 按钮区域
        self._create_buttons(layout)
    
    def _create_frame_selector(self):
        """创建帧选择器"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 标题
        title = QLabel("📋 第一步：选择包含目标人脸的视频帧")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # 帧信息和重新随机按钮的水平布局
        info_layout = QHBoxLayout()

        # 帧信息
        frame_count_text = f"视频共 {getattr(self, 'total_frames', len(self.frames))} 帧"
        if hasattr(self, 'total_frames') and self.total_frames > 200:
            frame_count_text += f"，当前显示随机抽取的 {len(self.frames)} 帧"
        else:
            frame_count_text += f"，显示所有 {len(self.frames)} 帧"

        self.frame_info_label = QLabel(frame_count_text + "，请拖动滚动条选择任意一帧")
        self.frame_info_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        info_layout.addWidget(self.frame_info_label)

        info_layout.addStretch()

        # 重新随机按钮（仅在超过200帧时显示）
        if hasattr(self, 'total_frames') and self.total_frames > 200:
            self.resample_button = QPushButton("🎲 重新随机100帧")
            self.resample_button.clicked.connect(self._reload_random_frames)
            self.resample_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            info_layout.addWidget(self.resample_button)

        layout.addLayout(info_layout)

        # 直接使用虚拟滚动组件，不需要额外的滚动区域
        self.frame_scroll_widget = VirtualFrameScrollWidget(self.frame_thumbnails, self._on_frame_selected)
        self.frame_scroll_widget.setMaximumHeight(200)
        self.frame_scroll_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 保存引用以便后续使用
        self.frame_widgets = self.frame_scroll_widget.visible_widgets

        layout.addWidget(self.frame_scroll_widget)

        return widget

    def _create_face_selector(self):
        """创建人脸选择器"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 标题
        self.face_title_label = QLabel("🎯 第二步：选择要替换的人脸（可多选）")
        self.face_title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(self.face_title_label)

        # 说明
        self.face_info_label = QLabel("请先选择一个视频帧，然后勾选要替换的人脸")
        self.face_info_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(self.face_info_label)

        # 滚动区域
        self.face_scroll_area = QScrollArea()
        self.face_scroll_area.setWidgetResizable(True)
        self.face_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.face_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 人脸容器
        self.faces_widget = QWidget()
        self.faces_layout = QGridLayout(self.faces_widget)
        self.faces_layout.setSpacing(15)

        self.face_scroll_area.setWidget(self.faces_widget)
        layout.addWidget(self.face_scroll_area)

        return widget

    def _create_buttons(self, parent_layout):
        """创建按钮区域"""
        button_layout = QHBoxLayout()

        # 全选按钮
        self.select_all_button = QPushButton("✅ 全选人脸")
        self.select_all_button.clicked.connect(self._select_all_faces)
        self.select_all_button.setEnabled(False)
        button_layout.addWidget(self.select_all_button)

        # 清除选择按钮
        self.clear_selection_button = QPushButton("❌ 清除选择")
        self.clear_selection_button.clicked.connect(self._clear_face_selection)
        self.clear_selection_button.setEnabled(False)
        button_layout.addWidget(self.clear_selection_button)

        button_layout.addStretch()

        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        button_layout.addWidget(cancel_button)

        # 确认按钮
        self.confirm_button = QPushButton("确认选择")
        self.confirm_button.clicked.connect(self._confirm_selection)
        self.confirm_button.setEnabled(False)
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.confirm_button)

        parent_layout.addLayout(button_layout)

    def _on_frame_selected(self, frame_index):
        """帧被选中"""
        # 设置新选择
        self.selected_frame_index = frame_index
        self.frame_scroll_widget.set_selected_frame(frame_index)

        # 更新帧信息
        actual_frame_idx, _ = self.frames[frame_index]
        self.frame_info_label.setText(f"已选择第 {actual_frame_idx + 1} 帧（共 {len(self.frames)} 帧）")

        # 分析该帧的人脸
        self._analyze_frame_faces(frame_index)

    def _analyze_frame_faces(self, frame_index):
        """分析指定帧的人脸"""
        try:
            # 重新读取指定帧（因为我们只保存了缩略图）
            actual_frame_idx, _ = self.frames[frame_index]
            cap = cv2.VideoCapture(str(self.video_path))
            cap.set(cv2.CAP_PROP_POS_FRAMES, actual_frame_idx)
            ret, frame = cap.read()
            cap.release()

            if not ret:
                self.face_info_label.setText("无法读取该帧，请选择其他帧")
                self._clear_face_widgets()
                return

            # 检测人脸
            face_info_list = self.face_swapper.get_faces_with_info(frame)

            if not face_info_list:
                self.face_info_label.setText("该帧中未检测到人脸，请选择其他帧")
                self._clear_face_widgets()
                return

            # 更新人脸信息
            self.face_info_label.setText(f"在该帧中检测到 {len(face_info_list)} 个人脸，请勾选要替换的人脸")

            # 提取人脸预览图
            face_previews = []
            for face_info in face_info_list:
                preview = self.face_swapper.extract_face_preview(frame, face_info)
                face_previews.append(preview)

            # 更新人脸选择器
            self._update_face_selector(face_info_list, face_previews)

        except Exception as e:
            logger.error(f"人脸分析失败: {e}")
            self.face_info_label.setText(f"人脸分析失败: {e}")
            self._clear_face_widgets()

    def _update_face_selector(self, face_info_list, face_previews):
        """更新人脸选择器"""
        # 清除旧的人脸组件
        self._clear_face_widgets()

        # 创建新的人脸组件
        self.current_faces = face_info_list
        cols = 4  # 每行4个人脸

        for i, (face_info, face_preview) in enumerate(zip(face_info_list, face_previews)):
            face_widget = FaceCheckboxWidget(face_info, face_preview, i)
            self.face_widgets.append(face_widget)

            row = i // cols
            col = i % cols
            self.faces_layout.addWidget(face_widget, row, col)

        # 启用按钮
        self.select_all_button.setEnabled(True)
        self.clear_selection_button.setEnabled(True)

    def _clear_face_widgets(self):
        """清除人脸组件"""
        for widget in self.face_widgets:
            widget.setParent(None)
            widget.deleteLater()
        self.face_widgets.clear()
        self.current_faces.clear()

        # 禁用按钮
        self.select_all_button.setEnabled(False)
        self.clear_selection_button.setEnabled(False)
        self.confirm_button.setEnabled(False)

    def _select_all_faces(self):
        """全选人脸"""
        for widget in self.face_widgets:
            widget.set_checked(True)
        self._update_confirm_button()

    def _clear_face_selection(self):
        """清除人脸选择"""
        for widget in self.face_widgets:
            widget.set_checked(False)
        self._update_confirm_button()

    def _update_confirm_button(self):
        """更新确认按钮状态"""
        selected_count = sum(1 for widget in self.face_widgets if widget.is_checked())
        self.confirm_button.setEnabled(selected_count > 0)

        if selected_count > 0:
            self.confirm_button.setText(f"确认选择 ({selected_count} 个人脸)")
        else:
            self.confirm_button.setText("确认选择")

    def _confirm_selection(self):
        """确认选择"""
        # 获取选中的人脸索引
        self.selected_face_indices = []
        for i, widget in enumerate(self.face_widgets):
            if widget.is_checked():
                self.selected_face_indices.append(i)

        if self.selected_face_indices:
            self.accept()
        else:
            QMessageBox.warning(self, "提示", "请至少选择一个人脸")

    def get_selected_frame_index(self):
        """获取选中的帧索引（实际帧号）"""
        if self.selected_frame_index < len(self.frames):
            actual_frame_idx, _ = self.frames[self.selected_frame_index]
            return actual_frame_idx
        return 0

    def get_selected_face_indices(self):
        """获取选中的人脸索引列表"""
        return self.selected_face_indices

    def get_selected_faces_info(self):
        """获取选中的人脸信息"""
        selected_faces = []
        for idx in self.selected_face_indices:
            if idx < len(self.current_faces):
                selected_faces.append(self.current_faces[idx])
        return selected_faces
