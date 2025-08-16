#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试GUI版本检测显示
"""

import sys
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QTextEdit, QPushButton
from PyQt5.QtCore import Qt

# 添加项目路径
sys.path.insert(0, '.')

from gui.startup_checker import StartupCheckerDialog
from utils.system_checker import SystemChecker

class TestVersionDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("版本检测测试")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        # 文本显示区域
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)
        
        # 测试按钮
        test_btn = QPushButton("测试版本检测")
        test_btn.clicked.connect(self.test_version_check)
        layout.addWidget(test_btn)
        
        # 启动GUI按钮
        gui_btn = QPushButton("启动原始GUI")
        gui_btn.clicked.connect(self.launch_original_gui)
        layout.addWidget(gui_btn)
        
        self.setLayout(layout)
        
        # 自动执行测试
        self.test_version_check()
    
    def test_version_check(self):
        """测试版本检测"""
        try:
            self.text_area.append("🔍 开始版本检测测试...")
            
            # 执行系统检测
            checker = SystemChecker()
            result = checker.check_all()
            
            # 创建检测对话框并测试版本兼容性方法
            dialog = StartupCheckerDialog()
            version_info = dialog._get_version_compatibility_info(result)
            
            self.text_area.append("\n" + "="*60)
            self.text_area.append("版本兼容性检测结果:")
            self.text_area.append("="*60)
            self.text_area.append(version_info)
            self.text_area.append("="*60)
            
            # 检查关键信息
            if '❌ CUDA 12.x版本与当前ONNX Runtime不兼容' in version_info:
                self.text_area.append("✅ 正确检测到CUDA不兼容问题")
            else:
                self.text_area.append("❌ 未检测到CUDA不兼容问题")
            
            if '❌ 存在关键兼容性问题' in version_info:
                self.text_area.append("✅ 正确识别存在兼容性问题")
            else:
                self.text_area.append("❌ 未识别兼容性问题")
                
            self.text_area.append("\n🎯 测试完成！")
            
        except Exception as e:
            self.text_area.append(f"❌ 测试失败: {e}")
    
    def launch_original_gui(self):
        """启动原始GUI"""
        try:
            dialog = StartupCheckerDialog()
            dialog.exec_()
        except Exception as e:
            self.text_area.append(f"❌ 启动GUI失败: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    dialog = TestVersionDialog()
    dialog.show()
    
    sys.exit(app.exec_())
