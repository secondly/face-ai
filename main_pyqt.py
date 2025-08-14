#!/usr/bin/env python3
"""
AI换脸应用程序主入口 - PyQt5版本
支持GUI和命令行两种模式
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """检查必要的依赖"""
    try:
        import cv2
        import numpy
        import insightface
        print("✅ 所有核心依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def check_pyqt5():
    """检查PyQt5是否安装"""
    try:
        from PyQt5.QtWidgets import QApplication
        print("✅ PyQt5已安装")
        return True
    except ImportError:
        print("❌ PyQt5未安装")
        print("请运行: pip install PyQt5")
        return False

def run_gui():
    """运行GUI模式"""
    if not check_pyqt5():
        input("按回车键退出...")
        return
        
    try:
        from gui.pyqt_gui import main as pyqt_main
        print("🎭 启动PyQt5现代化GUI界面...")
        pyqt_main()
    except ImportError as e:
        print(f"❌ GUI模块导入失败: {e}")
        print("请确保已安装PyQt5: pip install PyQt5")
        input("按回车键退出...")
    except Exception as e:
        print(f"❌ GUI启动失败: {e}")
        input("按回车键退出...")

def run_cli(args):
    """运行命令行模式"""
    try:
        from core.face_swapper import FaceSwapper
        
        print("🎭 AI换脸 - 命令行模式")
        print(f"源人脸: {args.source}")
        print(f"目标文件: {args.target}")
        print(f"输出文件: {args.output}")
        
        # 初始化换脸引擎
        print("正在初始化AI模型...")
        face_swapper = FaceSwapper()
        
        # 检查文件类型
        target_path = Path(args.target)
        if target_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.wmv']:
            # 处理视频
            print("开始处理视频...")
            success = face_swapper.process_video(args.source, args.target, args.output)
        else:
            # 处理图像
            print("开始处理图像...")
            success = face_swapper.process_image(args.source, args.target, args.output)
        
        if success:
            print(f"✅ 换脸完成！输出文件: {args.output}")
        else:
            print("❌ 换脸失败")
            
    except Exception as e:
        print(f"❌ 处理失败: {e}")

def main():
    """主函数"""
    print("🎭 AI换脸【秘灵】")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        input("按回车键退出...")
        return
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="AI换脸应用程序")
    parser.add_argument("--source", "-s", help="源人脸图像路径")
    parser.add_argument("--target", "-t", help="目标图像/视频路径")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--gui", action="store_true", help="启动GUI模式")
    
    args = parser.parse_args()
    
    # 判断运行模式
    if args.gui or (not args.source and not args.target):
        # GUI模式
        run_gui()
    else:
        # 命令行模式
        if not all([args.source, args.target, args.output]):
            print("❌ 命令行模式需要指定 --source, --target, --output 参数")
            parser.print_help()
            return
        
        run_cli(args)

if __name__ == "__main__":
    main()
