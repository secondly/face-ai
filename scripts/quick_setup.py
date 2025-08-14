#!/usr/bin/env python3
"""
快速设置脚本

一键完成环境检查、模型下载和验证。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from scripts.check_environment import main as check_env
    from scripts.download_models import download_models
    from scripts.verify_models import verify_models
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.prompt import Confirm, Prompt
except ImportError as e:
    print(f"导入错误: {e}")
    print("请先安装依赖: pip install rich")
    sys.exit(1)

console = Console()

def print_banner():
    """打印横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    Deep-Live-Cam 快速设置                    ║
    ║                                                              ║
    ║  🎭 一键换脸，无需训练，支持实时处理                          ║
    ║  🚀 自动环境检查、模型下载和验证                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold blue")

def check_environment_interactive():
    """交互式环境检查"""
    console.print("\n[bold yellow]步骤 1: 环境检查[/bold yellow]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("正在检查环境...", total=None)
        
        # 重定向输出到字符串
        import io
        from contextlib import redirect_stdout, redirect_stderr
        
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()
        
        try:
            with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
                env_ok = check_env()
            
            progress.update(task, description="环境检查完成")
        except Exception as e:
            progress.update(task, description=f"环境检查失败: {e}")
            env_ok = False
    
    if env_ok:
        console.print("✅ 环境检查通过", style="bold green")
    else:
        console.print("❌ 环境检查发现问题", style="bold red")
        console.print("\n详细信息:")
        console.print(output_buffer.getvalue())
        console.print(error_buffer.getvalue())
        
        if not Confirm.ask("是否继续设置？"):
            return False
    
    return True

def select_models():
    """选择要下载的模型"""
    console.print("\n[bold yellow]步骤 2: 选择模型[/bold yellow]")
    
    # 显示可用模型
    table = Table(title="可用模型")
    table.add_column("序号", style="cyan", no_wrap=True)
    table.add_column("模型名称", style="magenta")
    table.add_column("描述", style="green")
    table.add_column("大小", style="yellow")
    
    from scripts.download_models import MODELS_CONFIG
    
    models_list = list(MODELS_CONFIG.items())
    for i, (name, config) in enumerate(models_list, 1):
        table.add_row(
            str(i),
            name,
            config['description'],
            f"{config['size_mb']} MB"
        )
    
    console.print(table)
    
    # 预设选项
    console.print("\n预设选项:")
    console.print("1. 核心模型 (推荐) - InSwapper + SCRFD + ArcFace")
    console.print("2. 完整模型 - 包含所有模型")
    console.print("3. 自定义选择")
    
    choice = Prompt.ask("请选择", choices=["1", "2", "3"], default="1")
    
    if choice == "1":
        # 核心模型
        return ["inswapper_128.onnx", "scrfd_10g_bnkps.onnx", "arcface_r100.onnx"]
    elif choice == "2":
        # 所有模型
        return list(MODELS_CONFIG.keys())
    else:
        # 自定义选择
        console.print("\n请输入要下载的模型序号 (用逗号分隔，如: 1,2,3):")
        indices_str = Prompt.ask("模型序号")
        
        try:
            indices = [int(x.strip()) for x in indices_str.split(",")]
            selected_models = []
            for idx in indices:
                if 1 <= idx <= len(models_list):
                    selected_models.append(models_list[idx-1][0])
            return selected_models
        except ValueError:
            console.print("输入格式错误，使用核心模型", style="yellow")
            return ["inswapper_128.onnx", "scrfd_10g_bnkps.onnx", "arcface_r100.onnx"]

def download_models_interactive(models_list):
    """交互式模型下载"""
    console.print(f"\n[bold yellow]步骤 3: 下载模型[/bold yellow]")
    
    models_dir = PROJECT_ROOT / "models"
    
    # 显示下载信息
    total_size = 0
    from scripts.download_models import MODELS_CONFIG
    
    for model_name in models_list:
        if model_name in MODELS_CONFIG:
            total_size += MODELS_CONFIG[model_name]['size_mb']
    
    console.print(f"将下载 {len(models_list)} 个模型，总大小约 {total_size:.1f} MB")
    console.print(f"保存目录: {models_dir}")
    
    if not Confirm.ask("开始下载？"):
        return False
    
    # 执行下载
    with Progress(console=console) as progress:
        task = progress.add_task("下载模型...", total=100)
        
        try:
            success = download_models(
                models_dir=str(models_dir),
                models_list=models_list,
                force=False,
                verify=True
            )
            
            progress.update(task, completed=100)
            
            if success:
                console.print("✅ 模型下载完成", style="bold green")
            else:
                console.print("❌ 部分模型下载失败", style="bold red")
                show_alternative_methods()

            return success
            
        except Exception as e:
            console.print(f"❌ 下载过程中出错: {e}", style="bold red")
            show_alternative_methods()
            return False

def show_alternative_methods():
    """显示替代获取方法"""
    console.print("\n[bold cyan]替代获取方法:[/bold cyan]")

    console.print("\n1. 使用InsightFace自动下载 (推荐):")
    console.print("   pip install insightface")
    console.print("   python -c \"import insightface; app = insightface.app.FaceAnalysis(name='buffalo_l'); app.prepare(ctx_id=-1)\"")
    console.print("   # 然后从 ~/.insightface/models/ 复制文件到 models/")

    console.print("\n2. 手动下载:")
    console.print("   查看 '模型获取指南.md' 文件获取详细下载链接")

    console.print("\n3. 从其他项目复制:")
    console.print("   - FaceFusion: ~/.cache/facefusion/models/")
    console.print("   - Roop: ./models/")
    console.print("   - 其他换脸项目的模型目录")

    console.print("\n4. 使用命令行工具:")
    console.print("   wget 或 curl 直接下载 (参考模型获取指南)")

    console.print(f"\n[yellow]完成后运行验证:[/yellow] python scripts/verify_models.py")

def verify_models_interactive():
    """交互式模型验证"""
    console.print(f"\n[bold yellow]步骤 4: 验证模型[/bold yellow]")
    
    models_dir = PROJECT_ROOT / "models"
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("正在验证模型...", total=None)
        
        try:
            success = verify_models(
                models_dir=str(models_dir),
                test_inference=False  # 跳过推理测试以加快速度
            )
            
            progress.update(task, description="模型验证完成")
            
            if success:
                console.print("✅ 模型验证通过", style="bold green")
            else:
                console.print("❌ 模型验证发现问题", style="bold red")
            
            return success
            
        except Exception as e:
            console.print(f"❌ 验证过程中出错: {e}", style="bold red")
            return False

def show_next_steps():
    """显示后续步骤"""
    console.print("\n[bold green]🎉 设置完成！[/bold green]")
    
    next_steps = """
    [bold cyan]后续步骤:[/bold cyan]
    
    1. 测试基础功能:
       python -m dlc_batch.cli check-env
    
    2. 单视频换脸:
       python -m dlc_batch.cli swap-video --source face.jpg --input video.mp4 --output result.mp4
    
    3. 实时换脸:
       python -m dlc_batch.cli swap-live --source face.jpg --camera 0 --show-window
    
    4. 查看帮助:
       python -m dlc_batch.cli --help
    
    [bold yellow]注意事项:[/bold yellow]
    - 确保对使用的人脸图像拥有合法授权
    - 仅在合规场景下使用本工具
    - 遵守当地法律法规
    """
    
    console.print(Panel(next_steps, title="设置完成", border_style="green"))

def main():
    """主函数"""
    try:
        print_banner()
        
        # 步骤1: 环境检查
        if not check_environment_interactive():
            console.print("设置已取消", style="yellow")
            return
        
        # 步骤2: 选择模型
        models_to_download = select_models()
        if not models_to_download:
            console.print("未选择模型，设置已取消", style="yellow")
            return
        
        # 步骤3: 下载模型
        if not download_models_interactive(models_to_download):
            console.print("模型下载失败，请检查网络连接", style="red")
            return
        
        # 步骤4: 验证模型
        verify_models_interactive()
        
        # 显示后续步骤
        show_next_steps()
        
    except KeyboardInterrupt:
        console.print("\n用户中断设置", style="yellow")
    except Exception as e:
        console.print(f"设置过程中出错: {e}", style="red")

if __name__ == "__main__":
    main()
