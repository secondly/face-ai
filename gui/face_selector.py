#!/usr/bin/env python3
"""
人脸选择对话框
用于多人脸场景下选择要替换的特定人脸
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

class FacePreviewWidget(QFrame):
    """人脸预览组件"""
    
    clicked = pyqtSignal(int)  # 发送选中的人脸索引
    
    def __init__(self, face_info, face_image, index):
        super().__init__()
        self.face_info = face_info
        self.face_image = face_image
        self.index = index
        self.selected = False
        
        self._setup_ui()
        self._setup_style()
    
    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 人脸图像
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(150, 150)
        
        # 转换numpy图像为QPixmap
        if self.face_image is not None:
            height, width, channel = self.face_image.shape
            bytes_per_line = 3 * width
            q_image = QImage(self.face_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        
        layout.addWidget(self.image_label)
        
        # 人脸信息
        info_text = f"人脸 #{self.index + 1}\n"
        info_text += f"大小: {self.face_info['area']} 像素\n"
        info_text += f"位置: ({self.face_info['center'][0]}, {self.face_info['center'][1]})\n"
        info_text += f"置信度: {self.face_info['confidence']:.2f}"
        
        self.info_label = QLabel(info_text)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.info_label)
        
        # 选择按钮
        self.select_button = QPushButton("选择此人脸")
        self.select_button.clicked.connect(self._on_select)
        layout.addWidget(self.select_button)
    
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            FacePreviewWidget {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
                margin: 5px;
            }
            
            FacePreviewWidget:hover {
                border-color: #007acc;
                background-color: #f8f9fa;
            }
            
            QLabel {
                border: none;
                background-color: transparent;
            }
            
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            
            QPushButton:hover {
                background-color: #005a9e;
            }
            
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
    
    def _on_select(self):
        """选择此人脸"""
        self.clicked.emit(self.index)
    
    def set_selected(self, selected):
        """设置选中状态"""
        self.selected = selected
        if selected:
            self.setStyleSheet(self.styleSheet() + """
                FacePreviewWidget {
                    border: 3px solid #28a745;
                    background-color: #e8f5e8;
                }
                
                QPushButton {
                    background-color: #28a745;
                }
                
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            self.select_button.setText("✓ 已选择")
        else:
            self._setup_style()
            self.select_button.setText("选择此人脸")

class FaceSelectorDialog(QDialog):
    """人脸选择对话框"""
    
    def __init__(self, image_path, face_swapper=None, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.face_swapper = face_swapper or FaceSwapper()
        self.selected_index = -1
        self.face_widgets = []
        
        self.setWindowTitle("选择要替换的人脸")
        self.setModal(True)
        self.resize(800, 600)
        
        self._load_faces()
        self._setup_ui()
    
    def _load_faces(self):
        """加载并分析人脸"""
        try:
            # 读取图像
            image = cv2.imread(str(self.image_path))
            if image is None:
                raise ValueError("无法读取图像文件")
            
            # 检测人脸
            self.face_info_list = self.face_swapper.get_faces_with_info(image)
            
            if not self.face_info_list:
                QMessageBox.warning(self, "警告", "图像中未检测到人脸")
                self.reject()
                return
            
            # 提取人脸预览图
            self.face_previews = []
            for face_info in self.face_info_list:
                preview = self.face_swapper.extract_face_preview(image, face_info)
                self.face_previews.append(preview)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"人脸检测失败:\n{e}")
            self.reject()
    
    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel(f"检测到 {len(self.face_info_list)} 个人脸，请选择要替换的人脸：")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
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
        
        # 确认和取消按钮
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
