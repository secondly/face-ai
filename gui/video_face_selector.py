#!/usr/bin/env python3
"""
视频人脸选择对话框
用于从视频第一帧中选择要替换的特定人脸
"""

import sys
import cv2
import numpy as np
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QGridLayout, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QFont

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.face_swapper import FaceSwapper
from gui.face_selector import FacePreviewWidget

class VideoFaceSelectorDialog(QDialog):
    """视频人脸选择对话框"""
    
    def __init__(self, video_path, face_swapper=None, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.face_swapper = face_swapper or FaceSwapper()
        self.selected_index = -1
        self.face_widgets = []
        
        self.setWindowTitle("选择视频中要替换的人脸")
        self.setModal(True)
        self.resize(800, 600)
        
        self._load_first_frame_faces()
        self._setup_ui()
    
    def _load_first_frame_faces(self):
        """从视频第一帧加载并分析人脸"""
        try:
            # 打开视频
            cap = cv2.VideoCapture(str(self.video_path))
            if not cap.isOpened():
                raise ValueError("无法打开视频文件")
            
            # 读取第一帧
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                raise ValueError("无法读取视频第一帧")
            
            # 检测人脸
            self.face_info_list = self.face_swapper.get_faces_with_info(frame)
            
            if not self.face_info_list:
                QMessageBox.warning(self, "警告", "视频第一帧中未检测到人脸")
                self.reject()
                return
            
            # 提取人脸预览图
            self.face_previews = []
            for face_info in self.face_info_list:
                preview = self.face_swapper.extract_face_preview(frame, face_info)
                self.face_previews.append(preview)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"视频人脸检测失败:\n{e}")
            self.reject()
    
    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel(f"从视频第一帧检测到 {len(self.face_info_list)} 个人脸")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 说明文字
        info_label = QLabel("选择的人脸将在整个视频中被替换，其他人脸保持不变")
        info_label.setFont(QFont("Arial", 12))
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #666666; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 人脸网格容器
        faces_widget = QWidget()
        faces_layout = QGridLayout(faces_widget)
        faces_layout.setSpacing(15)
        
        # 创建人脸预览组件
        cols = 3  # 每行3个人脸
        for i, (face_info, face_preview) in enumerate(zip(self.face_info_list, self.face_previews)):
            face_widget = FacePreviewWidget(face_info, face_preview, i)
            face_widget.clicked.connect(self._on_face_selected)
            self.face_widgets.append(face_widget)
            
            row = i // cols
            col = i % cols
            faces_layout.addWidget(face_widget, row, col)
        
        scroll_area.setWidget(faces_widget)
        layout.addWidget(scroll_area)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 自动选择按钮
        auto_button = QPushButton("自动选择最大人脸")
        auto_button.clicked.connect(self._auto_select_largest)
        auto_button.setStyleSheet("""
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
        button_layout.addWidget(auto_button)
        
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
        self.confirm_button.clicked.connect(self.accept)
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
        
        layout.addLayout(button_layout)
        
        # 添加提示信息
        tip_label = QLabel("💡 提示：选择的人脸将通过位置和大小跟踪在整个视频中进行替换")
        tip_label.setFont(QFont("Arial", 10))
        tip_label.setStyleSheet("color: #007acc; background-color: #f0f8ff; padding: 10px; border-radius: 4px; margin-top: 10px;")
        tip_label.setWordWrap(True)
        layout.addWidget(tip_label)
    
    def _on_face_selected(self, index):
        """人脸被选中"""
        # 取消之前的选择
        for widget in self.face_widgets:
            widget.set_selected(False)
        
        # 设置新选择
        self.selected_index = index
        self.face_widgets[index].set_selected(True)
        self.confirm_button.setEnabled(True)
    
    def _auto_select_largest(self):
        """自动选择最大的人脸"""
        if self.face_info_list:
            # 第一个就是最大的（已经按大小排序）
            self._on_face_selected(0)
    
    def get_selected_index(self):
        """获取选中的人脸索引"""
        return self.selected_index
