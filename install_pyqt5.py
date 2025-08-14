#!/usr/bin/env python3
"""
PyQt5安装脚本
自动安装PyQt5并测试
"""

import subprocess
import sys

def install_pyqt5():
    """安装PyQt5"""
    print("🚀 正在安装PyQt5...")
    
    try:
        # 安装PyQt5
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt5>=5.15.0"])
        print("✅ PyQt5安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ PyQt5安装失败: {e}")
        return False

def test_pyqt5():
    """测试PyQt5"""
    print("🧪 测试PyQt5...")
    
    try:
        from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton
        from PyQt5.QtCore import Qt
        
        print("✅ PyQt5导入成功")
        
        # 创建测试应用
        app = QApplication(sys.argv)
        
        # 创建测试窗口
        window = QWidget()
        window.setWindowTitle("PyQt5测试")
        window.setGeometry(300, 300, 400, 200)
        
        layout = QVBoxLayout()
        
        label = QLabel("PyQt5工作正常！")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; font-weight: bold; color: #007acc;")
        layout.addWidget(label)
        
        button = QPushButton("关闭")
        button.clicked.connect(window.close)
        button.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        layout.addWidget(button)
        
        window.setLayout(layout)
        
        print("✅ 测试窗口创建成功")
        print("请关闭测试窗口继续...")
        
        window.show()
        app.exec_()
        return True
        
    except ImportError as e:
        print(f"❌ PyQt5导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ PyQt5测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🎨 PyQt5安装程序")
    print("=" * 40)
    
    # 检查是否已安装
    try:
        from PyQt5.QtWidgets import QApplication
        print("✅ PyQt5已安装")
        
        # 测试是否正常工作
        if test_pyqt5():
            print("\n🎉 PyQt5工作正常！")
            print("现在可以运行: python main_pyqt.py")
        else:
            print("\n❌ PyQt5测试失败")
            
    except ImportError:
        print("❌ PyQt5未安装")
        
        # 询问是否安装
        choice = input("是否现在安装PyQt5? (y/n): ").lower()
        if choice == 'y':
            if install_pyqt5():
                print("\n🎉 安装完成！")
                if test_pyqt5():
                    print("现在可以运行: python main_pyqt.py")
            else:
                print("\n❌ 安装失败")
        else:
            print("跳过安装")
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()
