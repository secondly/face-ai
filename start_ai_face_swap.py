#!/usr/bin/env python3
"""
AI换脸工具启动器 - 使用虚拟环境
"""

import subprocess
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).parent
    venv_python = project_root / "venv" / "Scripts" / "python.exe"
    main_script = project_root / "main_pyqt.py"
    
    if not venv_python.exists():
        print("❌ 虚拟环境不存在，请先运行 setup_venv.py")
        input("按回车键退出...")
        return 1
    
    if not main_script.exists():
        print("❌ 主程序文件不存在")
        input("按回车键退出...")
        return 1
    
    print("🎭 启动AI换脸工具...")
    print("🔧 使用虚拟环境:", venv_python.parent.parent)
    
    try:
        # 在虚拟环境中运行主程序
        result = subprocess.run([str(venv_python), str(main_script)])
        return result.returncode
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        input("按回车键退出...")
        return 1

if __name__ == "__main__":
    sys.exit(main())
