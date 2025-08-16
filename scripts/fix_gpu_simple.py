#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU问题简单修复脚本
避免Unicode字符，专注解决ONNX Runtime版本问题
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, timeout=300):
    """运行命令"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def fix_onnx_runtime():
    """修复ONNX Runtime版本"""
    print("开始修复ONNX Runtime版本...")
    print("=" * 50)

    # 检查当前conda环境
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', '')
    if conda_env == 'face-ai-cuda11':
        print(f"使用conda环境: {conda_env}")
        python_exe = sys.executable
        pip_exe = "pip"
    else:
        print(f"错误：当前环境是 {conda_env}，需要在 face-ai-cuda11 环境中运行")
        print("请先运行: conda activate face-ai-cuda11")
        return False
    
    # 步骤1: 卸载现有版本
    print("\n步骤1: 卸载现有ONNX Runtime版本")
    packages_to_remove = ['onnxruntime', 'onnxruntime-gpu', 'onnxruntime-directml']
    
    for package in packages_to_remove:
        print(f"卸载 {package}...")
        success, stdout, stderr = run_command([str(pip_exe), 'uninstall', package, '-y'])
        if success:
            print(f"成功卸载 {package}")
        else:
            print(f"卸载 {package} 失败或未安装")
    
    # 步骤2: 安装兼容版本
    print("\n步骤2: 安装兼容版本")
    target_version = "1.15.1"
    print(f"安装 onnxruntime-gpu=={target_version}...")

    success, stdout, stderr = run_command([
        str(pip_exe), 'install', f'onnxruntime-gpu=={target_version}',
        '--trusted-host', 'pypi.org',
        '--trusted-host', 'pypi.python.org',
        '--trusted-host', 'files.pythonhosted.org'
    ])
    
    if success:
        print(f"成功安装 onnxruntime-gpu=={target_version}")
    else:
        print(f"安装失败: {stderr}")
        return False
    
    # 步骤3: 验证安装
    print("\n步骤3: 验证安装")
    test_script = '''
import onnxruntime as ort
print(f"ONNX Runtime版本: {ort.__version__}")
providers = ort.get_available_providers()
print(f"可用提供者: {providers}")
if "CUDAExecutionProvider" in providers:
    print("CUDA提供者可用")
else:
    print("CUDA提供者不可用")
'''
    
    success, stdout, stderr = run_command([str(python_exe), '-c', test_script])
    
    if success:
        print("验证结果:")
        print(stdout)
        if "CUDA提供者可用" in stdout:
            print("修复成功！")
            return True
        else:
            print("CUDA提供者仍不可用")
            return False
    else:
        print(f"验证失败: {stderr}")
        return False

def check_current_status():
    """检查当前状态"""
    print("检查当前ONNX Runtime状态...")
    print("=" * 50)
    
    # 检查系统环境
    print("系统环境:")
    try:
        result = subprocess.run([sys.executable, '-c', '''
import onnxruntime as ort
print(f"版本: {ort.__version__}")
providers = ort.get_available_providers()
print(f"提供者: {providers}")
'''], capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"系统环境检查失败: {e}")
    
    # 检查虚拟环境
    venv_dir = Path(__file__).parent.parent / "venv"
    if venv_dir.exists():
        python_exe = venv_dir / "Scripts" / "python.exe"
        print(f"\n虚拟环境 ({venv_dir}):")
        try:
            result = subprocess.run([str(python_exe), '-c', '''
import onnxruntime as ort
print(f"版本: {ort.__version__}")
providers = ort.get_available_providers()
print(f"提供者: {providers}")
'''], capture_output=True, text=True)
            print(result.stdout)
        except Exception as e:
            print(f"虚拟环境检查失败: {e}")
    else:
        print("\n虚拟环境不存在")

def main():
    """主函数"""
    print("AI换脸工具 - GPU问题简单修复")
    print("=" * 60)
    
    # 检查当前状态
    check_current_status()
    
    # 询问是否修复
    print("\n是否要修复ONNX Runtime版本问题？")
    print("这将:")
    print("1. 卸载当前的ONNX Runtime")
    print("2. 安装兼容CUDA 12.3的版本 (1.16.3)")
    print("3. 验证GPU功能")
    
    choice = input("\n输入 y 继续，其他键取消: ").lower().strip()
    
    if choice == 'y':
        success = fix_onnx_runtime()
        if success:
            print("\n修复完成！")
            print("建议重启AI换脸工具以应用更改。")
        else:
            print("\n修复失败，请检查错误信息。")
    else:
        print("取消修复")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        input("\n按回车键退出...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n用户取消操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n脚本执行失败: {e}")
        input("\n按回车键退出...")
        sys.exit(1)
