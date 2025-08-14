#!/usr/bin/env python3
"""
AI换脸【秘灵】 - 主启动文件
智能换脸应用程序
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_models():
    """检查模型文件是否存在"""
    models_dir = Path("models")
    required_models = [
        "inswapper_128.onnx",
        "scrfd_10g_bnkps.onnx", 
        "arcface_r100.onnx"
    ]
    
    missing_models = []
    for model_name in required_models:
        model_path = models_dir / model_name
        if not model_path.exists():
            missing_models.append(model_name)
    
    if missing_models:
        print("❌ 缺少以下模型文件:")
        for model in missing_models:
            print(f"   • {model}")
        print("\n🔧 请运行以下命令获取模型:")
        print("   python scripts/simple_model_getter.py")
        return False
    
    print("✅ 所有模型文件已就绪")
    return True


def run_gui():
    """运行GUI界面"""
    try:
        from gui.face_swap_gui import FaceSwapGUI
        
        print("🎭 启动AI换脸GUI界面...")
        app = FaceSwapGUI()
        app.run()
        
    except ImportError as e:
        print(f"❌ 导入GUI模块失败: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ GUI启动失败: {e}")


def run_cli(args):
    """运行命令行界面"""
    try:
        from core.face_swapper import FaceSwapper
        
        print("🎭 启动AI换脸命令行模式...")
        
        # 初始化换脸引擎
        print("正在初始化AI模型...")
        face_swapper = FaceSwapper()
        print("✅ AI模型初始化完成")
        
        # 检查输入文件
        if not Path(args.source).exists():
            print(f"❌ 源人脸图像不存在: {args.source}")
            return
        
        if not Path(args.target).exists():
            print(f"❌ 目标文件不存在: {args.target}")
            return
        
        # 创建输出目录
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 判断处理类型
        target_ext = Path(args.target).suffix.lower()
        
        if target_ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv']:
            # 处理视频
            print(f"📹 开始处理视频: {args.target}")
            
            def progress_callback(progress, current_frame, total_frames):
                print(f"\r进度: {progress:.1f}% ({current_frame}/{total_frames} 帧)", end="")
            
            success = face_swapper.process_video(
                args.source, 
                args.target, 
                args.output,
                progress_callback=progress_callback
            )
            print()  # 换行
        else:
            # 处理图像
            print(f"🖼️ 开始处理图像: {args.target}")
            success = face_swapper.process_image(
                args.source,
                args.target,
                args.output
            )
        
        # 显示结果
        if success:
            print(f"🎉 换脸完成！输出文件: {args.output}")
        else:
            print("❌ 换脸失败")
            
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ 处理失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI换脸【秘灵】",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 启动GUI界面
  python main.py
  
  # 命令行处理图像
  python main.py --source face.jpg --target photo.jpg --output result.jpg
  
  # 命令行处理视频
  python main.py --source face.jpg --target video.mp4 --output result.mp4
  
  # 获取模型文件
  python scripts/simple_model_getter.py
        """
    )
    
    parser.add_argument('--source', '-s', 
                       help='源人脸图像路径')
    parser.add_argument('--target', '-t',
                       help='目标图像或视频路径')
    parser.add_argument('--output', '-o',
                       help='输出文件路径')
    parser.add_argument('--gui', action='store_true',
                       help='强制启动GUI界面')
    parser.add_argument('--check-models', action='store_true',
                       help='检查模型文件状态')
    
    args = parser.parse_args()
    
    print("🎭 AI换脸【秘灵】")
    print("=" * 40)
    
    # 检查模型状态
    if args.check_models:
        check_models()
        return
    
    # 检查模型文件
    if not check_models():
        return
    
    # 判断运行模式
    if args.gui or (not args.source and not args.target):
        # GUI模式
        run_gui()
    else:
        # 命令行模式
        if not args.source or not args.target or not args.output:
            print("❌ 命令行模式需要指定 --source, --target 和 --output 参数")
            print("使用 --help 查看详细用法")
            return
        
        run_cli(args)


if __name__ == "__main__":
    main()
