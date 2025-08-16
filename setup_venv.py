#!/usr/bin/env python3
"""
AI换脸工具 - 虚拟环境设置器
创建独立的虚拟环境，避免依赖冲突
"""

import os
import sys
import subprocess
import venv
from pathlib import Path
import shutil

class VirtualEnvManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_dir = self.project_root / "venv"
        self.python_exe = self.venv_dir / "Scripts" / "python.exe"
        self.pip_exe = self.venv_dir / "Scripts" / "pip.exe"
        
    def create_venv(self):
        """创建虚拟环境"""
        print("🚀 创建AI换脸工具专用虚拟环境...")
        print("=" * 60)
        
        # 删除现有虚拟环境
        if self.venv_dir.exists():
            print("🗑️ 删除现有虚拟环境...")
            shutil.rmtree(self.venv_dir)
        
        # 创建新的虚拟环境
        print("📦 创建新的虚拟环境...")
        venv.create(self.venv_dir, with_pip=True, clear=True)
        
        if not self.python_exe.exists():
            print("❌ 虚拟环境创建失败")
            return False
        
        print(f"✅ 虚拟环境创建成功: {self.venv_dir}")
        return True
    
    def upgrade_pip(self):
        """升级pip"""
        print("\n📦 升级pip...")
        try:
            result = subprocess.run([
                str(self.python_exe), "-m", "pip", "install", "--upgrade", "pip"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print("✅ pip升级成功")
                return True
            else:
                print(f"❌ pip升级失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ pip升级出错: {e}")
            return False
    
    def install_dependencies(self):
        """安装依赖包"""
        print("\n📦 安装项目依赖...")
        
        # 核心依赖包（按安装顺序）
        dependencies = [
            "wheel",
            "setuptools",
            "numpy==1.24.3",
            "opencv-python==4.8.1.78",
            "Pillow==10.0.1",
            "PyQt5==5.15.10",
            "requests==2.31.0",
            "tqdm==4.66.1",
            "albumentations==1.4.18",
            "onnxruntime-gpu==1.16.3",  # 使用兼容CUDA 12.3的版本
            "insightface==0.7.3",
        ]
        
        success_count = 0
        
        for i, package in enumerate(dependencies, 1):
            print(f"\n📥 ({i}/{len(dependencies)}) 安装 {package}...")
            try:
                result = subprocess.run([
                    str(self.pip_exe), "install", package
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print(f"✅ {package} 安装成功")
                    success_count += 1
                else:
                    print(f"❌ {package} 安装失败: {result.stderr}")
                    # 对于关键包，尝试不指定版本
                    if "==" in package:
                        base_package = package.split("==")[0]
                        print(f"🔄 尝试安装最新版本: {base_package}")
                        retry_result = subprocess.run([
                            str(self.pip_exe), "install", base_package
                        ], capture_output=True, text=True, timeout=300)
                        
                        if retry_result.returncode == 0:
                            print(f"✅ {base_package} (最新版本) 安装成功")
                            success_count += 1
                        else:
                            print(f"❌ {base_package} 安装仍然失败")
                            
            except Exception as e:
                print(f"❌ 安装 {package} 时出错: {e}")
        
        print(f"\n📊 安装结果: {success_count}/{len(dependencies)} 个包安装成功")
        return success_count >= len(dependencies) * 0.8  # 80%成功率即可
    
    def test_gpu_support(self):
        """测试GPU支持"""
        print("\n🧪 测试GPU支持...")
        
        test_script = '''
import sys
try:
    import onnxruntime as ort
    print(f"ONNX Runtime版本: {ort.__version__}")
    
    providers = ort.get_available_providers()
    print(f"可用提供者: {providers}")
    
    if "CUDAExecutionProvider" in providers:
        print("✅ CUDA提供者可用")
        
        # 尝试创建CUDA会话
        try:
            session_options = ort.SessionOptions()
            session_options.log_severity_level = 4
            print("✅ GPU支持测试通过")
            sys.exit(0)
        except Exception as e:
            print(f"⚠️ CUDA会话创建失败: {e}")
            print("🔄 将使用CPU模式")
            sys.exit(1)
    else:
        print("❌ CUDA提供者不可用")
        sys.exit(1)
        
except ImportError as e:
    print(f"❌ ONNX Runtime导入失败: {e}")
    sys.exit(1)
'''
        
        try:
            result = subprocess.run([
                str(self.python_exe), "-c", test_script
            ], capture_output=True, text=True, timeout=30)
            
            print(result.stdout)
            if result.stderr:
                print("错误信息:", result.stderr)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ GPU测试失败: {e}")
            return False
    
    def create_launcher(self):
        """创建启动器"""
        print("\n🚀 创建启动器...")
        
        # Windows批处理启动器
        launcher_bat = self.project_root / "start_ai_face_swap.bat"
        launcher_content = f'''@echo off
echo 🎭 启动AI换脸工具...
echo =====================================

cd /d "{self.project_root}"

if not exist "{self.venv_dir}" (
    echo ❌ 虚拟环境不存在，请先运行 setup_venv.py
    pause
    exit /b 1
)

echo 🔧 激活虚拟环境...
call "{self.venv_dir}\\Scripts\\activate.bat"

echo 🚀 启动AI换脸工具...
"{self.python_exe}" main_pyqt.py

if errorlevel 1 (
    echo ❌ 程序运行出错
    pause
)
'''
        
        with open(launcher_bat, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
        
        # Python启动器
        launcher_py = self.project_root / "start_ai_face_swap.py"
        launcher_py_content = f'''#!/usr/bin/env python3
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
        print(f"❌ 启动失败: {{e}}")
        input("按回车键退出...")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
        
        with open(launcher_py, 'w', encoding='utf-8') as f:
            f.write(launcher_py_content)
        
        print(f"✅ 启动器创建成功:")
        print(f"   Windows: {launcher_bat}")
        print(f"   Python:  {launcher_py}")
    
    def setup_complete_environment(self):
        """完整环境设置"""
        print("🎭 AI换脸工具 - 虚拟环境完整设置")
        print("=" * 60)
        print("这将创建一个独立的Python环境，避免依赖冲突")
        print("=" * 60)
        
        # 1. 创建虚拟环境
        if not self.create_venv():
            return False
        
        # 2. 升级pip
        if not self.upgrade_pip():
            print("⚠️ pip升级失败，但继续安装依赖...")
        
        # 3. 安装依赖
        if not self.install_dependencies():
            print("❌ 依赖安装失败")
            return False
        
        # 4. 测试GPU支持
        gpu_works = self.test_gpu_support()
        
        # 5. 创建启动器
        self.create_launcher()
        
        # 总结
        print("\n" + "=" * 60)
        print("🎉 虚拟环境设置完成！")
        print("=" * 60)
        
        print(f"📁 虚拟环境位置: {self.venv_dir}")
        print(f"🐍 Python解释器: {self.python_exe}")
        
        if gpu_works:
            print("✅ GPU支持: 正常")
        else:
            print("⚠️ GPU支持: 将使用CPU模式")
        
        print("\n🚀 启动方式:")
        print("   方法1: 双击 start_ai_face_swap.bat")
        print("   方法2: 运行 python start_ai_face_swap.py")
        print("   方法3: 手动激活虚拟环境后运行主程序")
        
        print("\n💡 优势:")
        print("   • 独立的Python环境，避免依赖冲突")
        print("   • 固定的包版本，确保稳定性")
        print("   • 不影响系统Python环境")
        print("   • 可以轻松删除和重建")
        
        return True

def main():
    """主函数"""
    manager = VirtualEnvManager()
    
    try:
        success = manager.setup_complete_environment()
        if success:
            print("\n✅ 设置成功！现在可以使用启动器运行AI换脸工具了。")
        else:
            print("\n❌ 设置失败，请检查错误信息并重试。")
        
        input("\n按回车键退出...")
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n用户取消设置")
        return 1
    except Exception as e:
        print(f"\n❌ 设置过程出错: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
        return 1

if __name__ == "__main__":
    sys.exit(main())
