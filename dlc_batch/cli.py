#!/usr/bin/env python3
"""
Deep-Live-Cam 命令行接口

提供swap-video, swap-dir, swap-live等命令。
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dlc_batch.config import get_default_config
from dlc_batch.utils import setup_logger

def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="dlc_batch",
        description="Deep-Live-Cam 实时换脸系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 单视频换脸
  python -m dlc_batch.cli swap-video --source face.jpg --input video.mp4 --output result.mp4
  
  # 批量处理
  python -m dlc_batch.cli swap-dir --source face.jpg --input-dir videos/ --output-dir results/
  
  # 实时换脸
  python -m dlc_batch.cli swap-live --source face.jpg --camera 0 --show-window
  
  # 下载模型
  python -m dlc_batch.cli download-models
  
  # 验证环境
  python -m dlc_batch.cli check-env
        """
    )
    
    # 全局参数
    parser.add_argument("--version", action="version", version="Deep-Live-Cam 1.0.0")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--log-file", help="日志文件路径")
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # swap-video 命令
    video_parser = subparsers.add_parser("swap-video", help="单视频换脸")
    video_parser.add_argument("--source", required=True, help="源脸图片路径")
    video_parser.add_argument("--input", required=True, help="输入视频路径")
    video_parser.add_argument("--output", required=True, help="输出视频路径")
    video_parser.add_argument("--quality", choices=["fast", "balanced", "high"], 
                             default="balanced", help="处理质量")
    video_parser.add_argument("--providers", nargs="+", default=["cuda", "cpu"],
                             help="推理提供者")
    video_parser.add_argument("--target", choices=["all", "largest", "first"],
                             default="largest", help="目标人脸选择")
    video_parser.add_argument("--conf-threshold", type=float, default=0.5,
                             help="检测置信度阈值")
    video_parser.add_argument("--enhance-face", action="store_true",
                             help="启用人脸增强")
    video_parser.add_argument("--color-correction", action="store_true",
                             help="启用颜色校正")
    video_parser.add_argument("--use-segmentation", action="store_true",
                             help="使用人脸分割")
    
    # swap-dir 命令
    dir_parser = subparsers.add_parser("swap-dir", help="批量视频处理")
    dir_parser.add_argument("--source", required=True, help="源脸图片路径")
    dir_parser.add_argument("--input-dir", required=True, help="输入视频目录")
    dir_parser.add_argument("--output-dir", required=True, help="输出视频目录")
    dir_parser.add_argument("--quality", choices=["fast", "balanced", "high"],
                           default="balanced", help="处理质量")
    dir_parser.add_argument("--providers", nargs="+", default=["cuda", "cpu"],
                           help="推理提供者")
    dir_parser.add_argument("--threads", type=int, default=1, help="并发线程数")
    dir_parser.add_argument("--extensions", nargs="+", 
                           default=[".mp4", ".mov", ".avi", ".mkv"],
                           help="支持的视频格式")
    
    # swap-live 命令
    live_parser = subparsers.add_parser("swap-live", help="实时换脸")
    live_parser.add_argument("--source", required=True, help="源脸图片路径")
    live_parser.add_argument("--camera", type=int, default=0, help="摄像头设备ID")
    live_parser.add_argument("--input-rtsp", help="RTSP输入流地址")
    live_parser.add_argument("--show-window", action="store_true", help="显示预览窗口")
    live_parser.add_argument("--record", help="录制输出文件路径")
    live_parser.add_argument("--rtmp", help="RTMP推流地址")
    live_parser.add_argument("--fps", type=int, default=30, help="目标帧率")
    live_parser.add_argument("--resolution", default="640x480", help="处理分辨率")
    
    # 工具命令
    subparsers.add_parser("download-models", help="下载模型文件")
    subparsers.add_parser("verify-models", help="验证模型文件")
    subparsers.add_parser("check-env", help="检查环境")
    
    return parser

def cmd_swap_video(args):
    """单视频换脸命令"""
    print(f"执行单视频换脸:")
    print(f"  源脸: {args.source}")
    print(f"  输入: {args.input}")
    print(f"  输出: {args.output}")
    print(f"  质量: {args.quality}")
    print(f"  提供者: {args.providers}")
    
    # TODO: 实现单视频换脸逻辑
    print("⚠ 功能开发中...")
    return False

def cmd_swap_dir(args):
    """批量视频处理命令"""
    print(f"执行批量视频处理:")
    print(f"  源脸: {args.source}")
    print(f"  输入目录: {args.input_dir}")
    print(f"  输出目录: {args.output_dir}")
    print(f"  线程数: {args.threads}")
    
    # TODO: 实现批量处理逻辑
    print("⚠ 功能开发中...")
    return False

def cmd_swap_live(args):
    """实时换脸命令"""
    print(f"执行实时换脸:")
    print(f"  源脸: {args.source}")
    print(f"  摄像头: {args.camera}")
    print(f"  显示窗口: {args.show_window}")
    
    # TODO: 实现实时换脸逻辑
    print("⚠ 功能开发中...")
    return False

def cmd_download_models(args):
    """下载模型命令"""
    print("下载模型文件...")
    
    try:
        from scripts.download_models import download_models
        models_dir = PROJECT_ROOT / "models"
        success = download_models(models_dir)
        return success
    except Exception as e:
        print(f"下载失败: {e}")
        return False

def cmd_verify_models(args):
    """验证模型命令"""
    print("验证模型文件...")
    
    try:
        from scripts.verify_models import verify_models
        models_dir = PROJECT_ROOT / "models"
        success = verify_models(models_dir)
        return success
    except Exception as e:
        print(f"验证失败: {e}")
        return False

def cmd_check_env(args):
    """检查环境命令"""
    print("检查运行环境...")
    
    try:
        from scripts.check_environment import main as check_main
        return check_main()
    except Exception as e:
        print(f"环境检查失败: {e}")
        return False

def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logger(
        level="DEBUG" if args.verbose else "INFO",
        log_file=args.log_file
    )
    
    # 如果没有指定命令，显示帮助
    if not args.command:
        parser.print_help()
        return 1
    
    # 执行对应命令
    command_map = {
        "swap-video": cmd_swap_video,
        "swap-dir": cmd_swap_dir,
        "swap-live": cmd_swap_live,
        "download-models": cmd_download_models,
        "verify-models": cmd_verify_models,
        "check-env": cmd_check_env,
    }
    
    if args.command in command_map:
        try:
            success = command_map[args.command](args)
            return 0 if success else 1
        except KeyboardInterrupt:
            print("\n用户中断操作")
            return 1
        except Exception as e:
            logger.error(f"执行命令失败: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    else:
        print(f"未知命令: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
