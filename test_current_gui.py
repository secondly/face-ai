#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试当前GUI是否使用了最新代码
"""

import sys
import os
import importlib

# 强制重新加载所有相关模块
modules_to_reload = [
    'gui.startup_checker',
    'utils.system_checker',
    'utils.gpu_detector'
]

for module_name in modules_to_reload:
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
        print(f"重新加载模块: {module_name}")

# 添加项目路径
sys.path.insert(0, '.')

from PyQt5.QtWidgets import QApplication
from gui.startup_checker import StartupCheckerDialog

def main():
    print("🔍 测试当前GUI版本检测...")
    
    app = QApplication(sys.argv)
    
    # 直接启动检测对话框
    dialog = StartupCheckerDialog()
    
    # 显示对话框
    result = dialog.exec_()
    
    if result == dialog.Accepted:
        print("✅ 用户点击了继续启动")
    else:
        print("❌ 用户取消了启动")

if __name__ == "__main__":
    main()
