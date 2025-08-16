#!/usr/bin/env python3
"""
AI换脸应用程序主入口 - PyQt5版本
支持GUI和命令行两种模式
"""

import sys
import argparse
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_cuda_environment():
    """检查是否在正确的CUDA环境中运行"""
    # 检查conda环境名称或项目内环境
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', '')
    python_path = sys.executable

    # 检查是否在项目内的cuda_env环境中
    project_cuda_env = os.path.join(os.path.dirname(__file__), 'cuda_env')
    is_project_env = project_cuda_env in python_path

    # 接受的环境：face-ai-cuda11 或项目内的cuda_env
    valid_envs = ['face-ai-cuda11']

    if conda_env not in valid_envs and not is_project_env:
        print("❌ 错误：请在CUDA虚拟环境中启动程序！")
        print()
        print("🔧 正确的启动方法：")
        print("方法1 (项目内环境):")
        print("1. conda activate ./cuda_env")
        print("2. python main_pyqt.py")
        print()
        print("方法2 (全局环境):")
        print("1. conda activate face-ai-cuda11")
        print("2. python main_pyqt.py")
        print()
        print("或者使用启动脚本：")
        print("双击 '启动AI换脸.bat'")
        print()
        print(f"当前环境: {conda_env if conda_env else '未知'}")
        print(f"Python路径: {python_path}")
        print("需要环境: face-ai-cuda11 或项目内的 cuda_env")
        print()
        print("💡 如果还没有创建环境，请参考 'CUDA虚拟环境使用说明.md'")
        sys.exit(1)

    if is_project_env:
        print(f"✅ 环境检测通过: 项目内CUDA环境")
    else:
        print(f"✅ 环境检测通过: {conda_env}")
    print(f"✅ Python路径: {python_path}")

# 在程序启动时检查环境
check_cuda_environment()

# 全局GPU配置
GPU_CONFIG = {
    'gpu_available': False,
    'recommended_config': {},
    'force_cpu': False
}

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

def check_gpu_environment():
    """检查GPU环境并返回推荐配置"""
    try:
        from utils.gpu_detector import GPUDetector

        print("\n" + "=" * 60)
        print("🔍 正在检测GPU环境...")
        print("=" * 60)

        detector = GPUDetector()
        gpu_result = detector.detect_all()

        # 打印详细报告
        detector.print_detailed_report(gpu_result)

        return gpu_result

    except ImportError as e:
        print(f"❌ GPU检测模块导入失败: {e}")
        return {
            'gpu_available': False,
            'recommended_config': {
                'type': 'cpu_only',
                'provider': 'CPUExecutionProvider',
                'description': 'CPU处理模式',
                'performance': 'basic',
                'gpu_enabled': False,
                'reason': 'GPU检测模块不可用'
            }
        }
    except Exception as e:
        print(f"❌ GPU环境检测失败: {e}")
        return {
            'gpu_available': False,
            'recommended_config': {
                'type': 'cpu_only',
                'provider': 'CPUExecutionProvider',
                'description': 'CPU处理模式',
                'performance': 'basic',
                'gpu_enabled': False,
                'reason': f'检测失败: {str(e)}'
            }
        }

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

def check_required_files():
    """检查必需文件是否存在"""
    try:
        from auto_downloader import AutoDownloader

        downloader = AutoDownloader()
        status = downloader.check_requirements()

        # 检查是否有缺失文件
        missing_files = []
        for category, files in status.items():
            for filename, exists in files.items():
                if not exists:
                    missing_files.append(f"{category}/{filename}")

        return len(missing_files) == 0, missing_files
    except Exception as e:
        print(f"检查文件时出错: {e}")
        return False, ["检查失败"]

def run_gui():
    """运行GUI模式"""
    if not check_pyqt5():
        # 在打包环境中不使用input()
        return

    try:
        # 创建QApplication实例（如果还没有的话）
        from PyQt5.QtWidgets import QApplication
        import sys

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
            app.setApplicationName("AI换脸工具")

        # 显示启动配置检测界面
        print("🔍 启动配置检测...")
        from gui.startup_checker import show_startup_checker

        if not show_startup_checker():
            print("⚠️ 用户取消启动或配置检测失败")
            return

        print("✅ 配置检测通过，继续启动...")

        # 检查必需文件
        print("🔍 检查必需文件...")
        files_complete, missing_files = check_required_files()

        if not files_complete:
            print(f"⚠️ 检测到缺失文件: {len(missing_files)} 个")
            print("启动下载管理器...")

            from gui.download_manager import show_download_manager
            download_success = show_download_manager()

            if not download_success:
                print("⚠️ 用户取消下载或下载失败")
                print("注意: 缺少必要文件可能导致功能异常")
                # 在打包环境中直接继续，不等待用户输入
                print("继续启动程序...")

        # 启动主程序
        from gui.pyqt_gui import main as pyqt_main
        print("🎭 启动PyQt5现代化GUI界面...")
        pyqt_main(gpu_config=GPU_CONFIG)

    except ImportError as e:
        print(f"❌ GUI模块导入失败: {e}")
        print("请确保已安装PyQt5: pip install PyQt5")
        # 在打包环境中不使用input()
        return
    except Exception as e:
        print(f"❌ GUI启动失败: {e}")
        # 在打包环境中不使用input()
        return

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
        # 在打包环境中不使用input()
        return

    # 检查GPU环境
    gpu_result = check_gpu_environment()

    # 解析命令行参数
    parser = argparse.ArgumentParser(description="AI换脸应用程序")
    parser.add_argument("--source", "-s", help="源人脸图像路径")
    parser.add_argument("--target", "-t", help="目标图像/视频路径")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--gui", action="store_true", help="启动GUI模式")
    parser.add_argument("--cpu-only", action="store_true", help="强制使用CPU模式")

    args = parser.parse_args()

    # 设置全局GPU配置
    global GPU_CONFIG
    GPU_CONFIG = {
        'gpu_available': gpu_result.get('gpu_available', False) and not args.cpu_only,
        'recommended_config': gpu_result.get('recommended_config', {}),
        'force_cpu': args.cpu_only
    }

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
