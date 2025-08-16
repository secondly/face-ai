#!/usr/bin/env python3
"""
启动前配置检测界面
在软件启动前检测所有配置项并提供解决方案
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QTextEdit, QProgressBar, 
                             QScrollArea, QWidget, QFrame, QMessageBox,
                             QTabWidget, QTreeWidget, QTreeWidgetItem,
                             QSplitter, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class CheckerWorker(QThread):
    """配置检测工作线程"""
    progress_updated = pyqtSignal(str, int)  # 消息, 进度
    check_completed = pyqtSignal(dict)  # 检测结果
    
    def run(self):
        """执行检测"""
        try:
            from utils.system_checker import SystemChecker
            
            checker = SystemChecker()
            
            # 逐步检测各个组件
            self.progress_updated.emit("🔍 检测系统信息...", 10)
            
            self.progress_updated.emit("🐍 检测Python环境...", 20)
            
            self.progress_updated.emit("📦 检测依赖包...", 40)
            
            self.progress_updated.emit("🎮 检测GPU配置...", 60)
            
            self.progress_updated.emit("🤖 检测模型文件...", 80)
            
            self.progress_updated.emit("🎬 检测FFmpeg...", 90)
            
            # 执行完整检测
            result = checker.check_all()
            
            self.progress_updated.emit("✅ 检测完成", 100)
            self.check_completed.emit(result)
            
        except Exception as e:
            error_result = {
                'overall_status': 'error',
                'issues': [f'检测过程出错: {str(e)}'],
                'recommendations': ['请检查系统环境并重试']
            }
            self.check_completed.emit(error_result)

class StartupCheckerDialog(QDialog):
    """启动配置检测对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.check_result = None
        self.worker = None

        # 检查CUDA环境
        self._check_cuda_environment()

        self.setWindowTitle("🔍 AI换脸工具 - 配置检测")
        self.setFixedSize(900, 700)
        self.setModal(True)

    def _check_cuda_environment(self):
        """检查CUDA环境并显示提示"""
        import os
        import sys
        conda_env = os.environ.get('CONDA_DEFAULT_ENV', '')
        python_path = sys.executable

        # 检查是否在项目内的cuda_env环境中
        project_cuda_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cuda_env')
        is_project_env = project_cuda_env in python_path

        # 检查conda环境名称是否包含cuda_env路径
        is_conda_project_env = conda_env and 'cuda_env' in conda_env

        # 调试信息
        print(f"DEBUG: conda_env = '{conda_env}'")
        print(f"DEBUG: python_path = '{python_path}'")
        print(f"DEBUG: project_cuda_env = '{project_cuda_env}'")
        print(f"DEBUG: is_project_env = {is_project_env}")
        print(f"DEBUG: is_conda_project_env = {is_conda_project_env}")

        # 接受的环境：face-ai-cuda11 或项目内的cuda_env
        valid_envs = ['face-ai-cuda11']

        if conda_env not in valid_envs and not is_project_env and not is_conda_project_env:
            from PyQt5.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("⚠️ 环境警告")
            msg.setText("检测到您不在推荐的CUDA环境中运行！")
            msg.setInformativeText(
                f"当前环境: {conda_env if conda_env else '未知'}\n"
                f"推荐环境: face-ai-cuda11 或项目内的 cuda_env\n\n"
                f"为了获得最佳GPU加速性能，建议：\n"
                f"方法1 (项目内环境):\n"
                f"1. conda activate ./cuda_env\n"
                f"2. python main_pyqt.py\n\n"
                f"方法2 (全局环境):\n"
                f"1. conda activate face-ai-cuda11\n"
                f"2. python main_pyqt.py\n\n"
                f"继续使用当前环境可能导致GPU加速不可用。"
            )
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msg.setDefaultButton(QMessageBox.Cancel)

            if msg.exec_() == QMessageBox.Cancel:
                sys.exit(0)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        
        self._setup_ui()
        
        # 自动开始检测
        QTimer.singleShot(500, self._start_check)
    
    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("🔍 正在检测系统配置...")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("准备开始检测...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 概览标签页
        self.overview_tab = self._create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "📋 概览")
        
        # 详细信息标签页
        self.details_tab = self._create_details_tab()
        self.tab_widget.addTab(self.details_tab, "🔍 详细信息")
        
        # 解决方案标签页
        self.solutions_tab = self._create_solutions_tab()
        self.tab_widget.addTab(self.solutions_tab, "💡 解决方案")

        # CUDA诊断标签页
        self.cuda_tab = self._create_cuda_tab()
        self.tab_widget.addTab(self.cuda_tab, "🔧 CUDA诊断")
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.recheck_button = QPushButton("🔄 重新检测")
        self.recheck_button.clicked.connect(self._start_check)
        self.recheck_button.setEnabled(False)
        button_layout.addWidget(self.recheck_button)
        
        button_layout.addStretch()
        
        self.continue_button = QPushButton("▶️ 继续启动")
        self.continue_button.clicked.connect(self.accept)
        self.continue_button.setEnabled(False)
        button_layout.addWidget(self.continue_button)
        
        self.exit_button = QPushButton("❌ 退出")
        self.exit_button.clicked.connect(self.reject)
        button_layout.addWidget(self.exit_button)
        
        layout.addLayout(button_layout)
    
    def _create_overview_tab(self):
        """创建概览标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 系统状态组
        self.system_group = QGroupBox("💻 系统状态")
        system_layout = QVBoxLayout(self.system_group)
        self.system_status_label = QTextEdit("检测中...")
        self.system_status_label.setReadOnly(True)
        self.system_status_label.setMaximumHeight(200)  # 限制高度，允许滚动
        system_layout.addWidget(self.system_status_label)
        layout.addWidget(self.system_group)
        
        # GPU状态组
        self.gpu_group = QGroupBox("🎮 GPU状态")
        gpu_layout = QVBoxLayout(self.gpu_group)
        self.gpu_status_label = QLabel("检测中...")
        gpu_layout.addWidget(self.gpu_status_label)
        layout.addWidget(self.gpu_group)
        
        # 问题列表组
        self.issues_group = QGroupBox("❌ 发现的问题")
        issues_layout = QVBoxLayout(self.issues_group)
        self.issues_text = QTextEdit()
        self.issues_text.setMaximumHeight(150)
        self.issues_text.setPlainText("检测中...")
        issues_layout.addWidget(self.issues_text)
        layout.addWidget(self.issues_group)
        
        layout.addStretch()
        return widget
    
    def _create_details_tab(self):
        """创建详细信息标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.details_tree = QTreeWidget()
        self.details_tree.setHeaderLabels(["项目", "状态", "详细信息"])
        self.details_tree.setColumnWidth(0, 200)
        self.details_tree.setColumnWidth(1, 100)
        layout.addWidget(self.details_tree)
        
        return widget
    
    def _create_solutions_tab(self):
        """创建解决方案标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.solutions_text = QTextEdit()
        self.solutions_text.setPlainText("检测完成后将显示解决方案...")
        layout.addWidget(self.solutions_text)

        return widget

    def _start_check(self):
        """开始检测"""
        if self.worker and self.worker.isRunning():
            return

        # 重置界面
        self.progress_bar.setValue(0)
        self.status_label.setText("正在检测...")
        self.continue_button.setEnabled(False)
        self.recheck_button.setEnabled(False)

        # 清空结果显示
        self.system_status_label.setPlainText("检测中...")
        self.gpu_status_label.setText("检测中...")
        self.issues_text.setPlainText("检测中...")
        self.details_tree.clear()
        self.solutions_text.setPlainText("检测中...")

        # 启动检测线程
        self.worker = CheckerWorker()
        self.worker.progress_updated.connect(self._update_progress)
        self.worker.check_completed.connect(self._on_check_completed)
        self.worker.start()

    def _update_progress(self, message: str, progress: int):
        """更新进度"""
        self.status_label.setText(message)
        self.progress_bar.setValue(progress)

    def _on_check_completed(self, result: dict):
        """检测完成"""
        self.check_result = result
        self.recheck_button.setEnabled(True)

        # 更新概览信息
        self._update_overview(result)

        # 更新详细信息
        self._update_details(result)

        # 更新解决方案
        self._update_solutions(result)

        # 根据检测结果决定是否允许继续
        overall_status = result.get('overall_status', 'error')
        if overall_status in ['excellent', 'good', 'warning']:
            self.continue_button.setEnabled(True)
            self.status_label.setText("✅ 检测完成，可以继续启动")
        else:
            self.continue_button.setEnabled(False)
            self.status_label.setText("❌ 检测发现严重问题，建议先解决后再启动")

    def _update_overview(self, result: dict):
        """更新概览信息"""
        # 系统状态
        system_info = result.get('system_info', {})
        python_env = result.get('python_env', {})

        # 只显示基本系统信息
        try:
            import onnxruntime as ort
            onnx_version = ort.__version__
        except:
            onnx_version = "未安装"

        try:
            import insightface
            insightface_version = insightface.__version__
        except:
            insightface_version = "未安装"

        system_text = f"""
💻 操作系统: {system_info.get('os', 'Unknown')} {system_info.get('architecture', '')}
🐍 Python版本: {system_info.get('python_version', 'Unknown')}
📦 虚拟环境: {'是' if python_env.get('in_virtual_env', False) else '否'}

📋 已安装组件版本:
🚀 CUDA: 12.3
🧠 ONNX Runtime: {onnx_version}
👤 InsightFace: {insightface_version}
        """.strip()
        self.system_status_label.setPlainText(system_text)

        # GPU状态
        gpu_config = result.get('gpu_config', {})
        if gpu_config.get('gpu_available', False):
            recommended = gpu_config.get('recommended_config', {})
            gpu_text = f"""
🎮 GPU加速: ✅ 可用
🚀 推荐配置: {recommended.get('description', 'Unknown')}
📊 性能等级: {recommended.get('performance', 'Unknown')}
💡 提供者: {recommended.get('provider', 'Unknown')}
            """.strip()
        else:
            gpu_text = """
🎮 GPU加速: ❌ 不可用
💻 将使用CPU模式（性能较慢）
            """.strip()
        self.gpu_status_label.setText(gpu_text)

        # 问题列表（包含版本兼容性问题）
        issues = result.get('issues', [])

        # 添加版本兼容性问题
        compatibility_issues = self._get_compatibility_issues(result)
        issues.extend(compatibility_issues)

        if issues:
            issues_text = "\n".join([f"• {issue}" for issue in issues])
        else:
            issues_text = "✅ 未发现问题"
        self.issues_text.setPlainText(issues_text)

    def _get_compatibility_issues(self, result: dict) -> list:
        """获取版本兼容性问题列表，包含详细的问题描述、原因和解决方案"""
        issues = []

        try:
            # CUDA环境兼容性检查
            try:
                # 检查当前conda环境
                conda_env = os.environ.get('CONDA_DEFAULT_ENV', '')
                python_path = sys.executable

                # 检查是否在项目内的cuda_env环境中
                project_cuda_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cuda_env')
                is_project_env = project_cuda_env in python_path

                # 检查conda环境名称是否包含cuda_env路径
                is_conda_project_env = conda_env and 'cuda_env' in conda_env

                valid_envs = ['face-ai-cuda11']

                if conda_env not in valid_envs and not is_project_env and not is_conda_project_env:
                    # 不在推荐环境中，检查系统级CUDA
                    import subprocess
                    result_cuda = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=5)
                    if result_cuda.returncode == 0 and 'release 12' in result_cuda.stdout:
                        issues.append("🚨 CUDA版本兼容性问题")
                        issues.append("   问题: CUDA 12.3与ONNX Runtime 1.17.1不兼容")
                        issues.append("   原因: 这是导致GPU无法工作的根本原因")
                        issues.append("   表现: LoadLibrary failed with error 126")
                        issues.append("   影响: GPU加速已自动降级到CPU模式")
                        issues.append("   解决方案: 使用face-ai-cuda11环境或项目内cuda_env环境")
                        issues.append("")
                else:
                    # 在推荐环境中，检查GPU是否正常工作
                    gpu_config = result.get('gpu_config', {})
                    if not gpu_config.get('gpu_available', False):
                        issues.append("⚠️ GPU配置问题")
                        issues.append("   问题: 在CUDA 11.8环境中但GPU加速不可用")
                        issues.append("   可能原因: 模型加载失败或显存不足")
                        issues.append("   解决方案: 检查显存使用情况或重启程序")
                        issues.append("")
            except:
                pass

            # 检查ONNX Runtime CUDA提供者
            try:
                import onnxruntime as ort
                providers = ort.get_available_providers()
                if 'CUDAExecutionProvider' not in providers:
                    issues.append("⚠️ ONNX Runtime CUDA提供者不可用")
                    issues.append("   解决方案: 重新安装onnxruntime-gpu")
                    issues.append("")
            except ImportError:
                issues.append("❌ ONNX Runtime未安装")
                issues.append("   解决方案: pip install onnxruntime-gpu")
                issues.append("")
            except:
                pass

        except Exception as e:
            issues.append(f"❌ 版本兼容性检查失败: {e}")

        return issues

    def _get_version_compatibility_info(self, result: dict) -> str:
        """获取版本兼容性信息"""
        try:
            compatibility_info = []

            # 定义项目预期版本（明确兼容性要求）
            expected_versions = {
                'python': '3.8+',
                'cuda': '11.8 (推荐) | 12.x (不兼容)',
                'cudnn': '8.x',
                'onnxruntime': '1.16+ 或 1.17+',
                'torch': '2.0+ (可选)',
                'insightface': '0.7+'
            }

            # Python版本检查
            system_info = result.get('system_info', {})
            python_version = system_info.get('python_version', 'Unknown')
            compatibility_info.append(f"🐍 Python: {python_version} (预期: {expected_versions['python']})")

            # CUDA版本检查
            try:
                import subprocess
                result_cuda = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=5)
                if result_cuda.returncode == 0:
                    import re
                    match = re.search(r'release (\d+\.\d+)', result_cuda.stdout)
                    if match:
                        cuda_ver = match.group(1)
                        compatibility_info.append(f"🚀 CUDA: {cuda_ver} (预期: {expected_versions['cuda']})")
                    else:
                        compatibility_info.append(f"🚀 CUDA: 已安装但版本检测失败 (预期: {expected_versions['cuda']})")
                else:
                    compatibility_info.append(f"❌ CUDA: 未安装或nvcc不可用 (预期: {expected_versions['cuda']})")
            except Exception:
                # 尝试从GPU配置中获取
                gpu_config = result.get('gpu_config', {})
                cuda_info = gpu_config.get('cuda', {})
                if cuda_info.get('available'):
                    cuda_version = cuda_info.get('version', 'Unknown')
                    if 'release' in cuda_version.lower():
                        import re
                        match = re.search(r'(\d+\.\d+)', cuda_version)
                        if match:
                            cuda_ver = match.group(1)
                            compatibility_info.append(f"🚀 CUDA: {cuda_ver} (预期: {expected_versions['cuda']})")
                        else:
                            compatibility_info.append(f"🚀 CUDA: {cuda_version} (预期: {expected_versions['cuda']})")
                    else:
                        compatibility_info.append(f"🚀 CUDA: {cuda_version} (预期: {expected_versions['cuda']})")
                else:
                    compatibility_info.append(f"❌ CUDA: 未检测到 (预期: {expected_versions['cuda']})")

            # ONNX Runtime版本检查
            try:
                import onnxruntime as ort
                onnx_version = ort.__version__
                compatibility_info.append(f"🧠 ONNX Runtime: {onnx_version} (预期: {expected_versions['onnxruntime']})")

                # 检查CUDA提供者兼容性
                providers = ort.get_available_providers()
                if 'CUDAExecutionProvider' in providers:
                    compatibility_info.append("✅ ONNX CUDA提供者: 可用")
                else:
                    compatibility_info.append("❌ ONNX CUDA提供者: 不可用")
            except ImportError:
                compatibility_info.append(f"❌ ONNX Runtime: 未安装 (预期: {expected_versions['onnxruntime']})")
            except Exception as e:
                compatibility_info.append(f"⚠️ ONNX Runtime: 检测失败 - {e}")

            # InsightFace版本检查
            try:
                import insightface
                insightface_version = insightface.__version__
                compatibility_info.append(f"👤 InsightFace: {insightface_version} (预期: {expected_versions['insightface']})")
            except ImportError:
                compatibility_info.append(f"❌ InsightFace: 未安装 (预期: {expected_versions['insightface']})")
            except:
                compatibility_info.append(f"⚠️ InsightFace: 版本检测失败 (预期: {expected_versions['insightface']})")

            # PyTorch版本检查（可选）
            try:
                import torch
                torch_version = torch.__version__
                compatibility_info.append(f"🔥 PyTorch: {torch_version} (预期: {expected_versions['torch']})")

                # 检查CUDA支持
                if torch.cuda.is_available():
                    torch_cuda_version = torch.version.cuda
                    compatibility_info.append(f"🔥 PyTorch CUDA: {torch_cuda_version} (可用)")
                else:
                    compatibility_info.append("❌ PyTorch CUDA: 不可用")
            except ImportError:
                compatibility_info.append(f"⚠️ PyTorch: 未安装 (预期: {expected_versions['torch']})")
            except:
                compatibility_info.append(f"⚠️ PyTorch: 版本检测失败")

            # 兼容性分析
            compatibility_info.append("\n🔍 兼容性分析:")

            # 检查关键兼容性问题
            issues = []
            cuda_onnx_compatible = True

            # Python版本检查
            if python_version.startswith('3.8') or python_version.startswith('3.9') or python_version.startswith('3.10'):
                compatibility_info.append("✅ Python版本兼容")
            else:
                issues.append("Python版本可能不兼容")
                compatibility_info.append("⚠️ Python版本可能不兼容")

            # 🚨 重要：CUDA版本兼容性检查
            compatibility_info.append("\n🚨 关键兼容性检查:")

            # CUDA环境兼容性检查
            try:
                # 检查当前conda环境
                conda_env = os.environ.get('CONDA_DEFAULT_ENV', '')
                python_path = sys.executable

                # 检查是否在项目内的cuda_env环境中
                project_cuda_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cuda_env')
                is_project_env = project_cuda_env in python_path

                # 检查conda环境名称是否包含cuda_env路径
                is_conda_project_env = conda_env and 'cuda_env' in conda_env

                valid_envs = ['face-ai-cuda11']

                if conda_env in valid_envs or is_project_env or is_conda_project_env:
                    if is_project_env:
                        compatibility_info.append("✅ 运行在项目内CUDA环境中")
                        compatibility_info.append("🎯 这是推荐的项目配置环境")
                    else:
                        compatibility_info.append("✅ 运行在CUDA 11.8兼容环境中")
                        compatibility_info.append("🎯 这是推荐的配置环境")

                    # 检查ONNX Runtime版本
                    try:
                        import onnxruntime as ort
                        onnx_version = ort.__version__
                        if onnx_version.startswith('1.15'):
                            compatibility_info.append("✅ ONNX Runtime 1.15.x与CUDA 11.8完全兼容")
                        else:
                            compatibility_info.append(f"⚠️ ONNX Runtime {onnx_version}，建议使用1.15.x")
                    except:
                        pass
                else:
                    # 检查系统级CUDA（如果不在推荐环境中）
                    import subprocess
                    result_cuda = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=5)
                    if result_cuda.returncode == 0 and 'release 12' in result_cuda.stdout:
                        compatibility_info.append("🚨 CUDA 12.x版本与ONNX Runtime 1.17.x不兼容！")
                        compatibility_info.append("❌ 这是GPU无法工作的根本原因")
                        compatibility_info.append("💡 解决方案: 使用face-ai-cuda11环境或项目内cuda_env环境")
                        issues.append("CUDA版本不兼容")
                        cuda_onnx_compatible = False
                    elif result_cuda.returncode == 0 and 'release 11.8' in result_cuda.stdout:
                        compatibility_info.append("✅ CUDA 11.8版本兼容")
                    else:
                        compatibility_info.append("⚠️ CUDA版本检测失败或未知版本")
            except:
                compatibility_info.append("⚠️ CUDA版本检测失败")

            # CUDA + ONNX Runtime兼容性检查
            try:
                import onnxruntime as ort
                onnx_version = ort.__version__
                providers = ort.get_available_providers()

                if 'CUDAExecutionProvider' in providers:
                    # 检查CUDA版本与ONNX Runtime的兼容性
                    try:
                        import subprocess
                        result_cuda = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=5)
                        cuda_version_str = result_cuda.stdout if result_cuda.returncode == 0 else ""

                        if '1.17' in onnx_version and 'release 12' in cuda_version_str:
                            issues.append("CUDA 12.x + ONNX Runtime 1.17.x 存在已知兼容性问题")
                            compatibility_info.append("❌ CUDA 12.x + ONNX Runtime 1.17.x 兼容性问题")
                            compatibility_info.append("💡 建议: 降级到CUDA 11.8 或使用CPU模式")
                            cuda_onnx_compatible = False
                        elif '1.16' in onnx_version and 'release 12' in cuda_version_str:
                            issues.append("CUDA 12.x + ONNX Runtime 1.16.x 存在兼容性问题")
                            compatibility_info.append("❌ CUDA 12.x + ONNX Runtime 1.16.x 兼容性问题")
                            compatibility_info.append("💡 建议: 降级到CUDA 11.8 或使用CPU模式")
                            cuda_onnx_compatible = False
                        else:
                            compatibility_info.append("✅ CUDA + ONNX Runtime 版本兼容")
                    except:
                        compatibility_info.append("⚠️ CUDA版本检测失败，无法判断兼容性")
                        cuda_onnx_compatible = False
                else:
                    compatibility_info.append("⚠️ ONNX Runtime CUDA提供者不可用")
                    cuda_onnx_compatible = False
            except ImportError:
                compatibility_info.append("⚠️ ONNX Runtime未安装")
                cuda_onnx_compatible = False

            # 最终兼容性总结
            if not issues and cuda_onnx_compatible:
                compatibility_info.append("🎉 所有版本兼容性检查通过")
                compatibility_info.append("✅ GPU加速应该可以正常工作")
            elif not cuda_onnx_compatible:
                compatibility_info.append("❌ 存在关键兼容性问题")
                compatibility_info.append("⚠️ GPU加速将自动降级到CPU模式")
                compatibility_info.append("🔧 解决方案: 降级CUDA到11.8版本")
            else:
                compatibility_info.append("⚠️ 存在一些兼容性问题")
                compatibility_info.append("💡 建议检查相关组件版本")

            return '\n'.join(compatibility_info)

        except Exception as e:
            return f"版本兼容性检查失败: {e}"

    def _update_details(self, result: dict):
        """更新详细信息"""
        self.details_tree.clear()

        # 系统信息
        system_item = QTreeWidgetItem(["💻 系统信息", "✅", ""])
        self.details_tree.addTopLevelItem(system_item)

        system_info = result.get('system_info', {})
        for key, value in system_info.items():
            if key != 'status':
                child = QTreeWidgetItem([key, "", str(value)])
                system_item.addChild(child)

        # Python环境
        python_env = result.get('python_env', {})
        status_icon = "✅" if python_env.get('status') == 'ok' else "⚠️"
        python_item = QTreeWidgetItem(["🐍 Python环境", status_icon, ""])
        self.details_tree.addTopLevelItem(python_item)

        for key, value in python_env.items():
            if key not in ['status', 'issues']:
                child = QTreeWidgetItem([key, "", str(value)])
                python_item.addChild(child)

        # 依赖包
        dependencies = result.get('dependencies', {})
        dep_status = "✅" if dependencies.get('status') == 'ok' else "❌"
        dep_item = QTreeWidgetItem(["📦 依赖包", dep_status, ""])
        self.details_tree.addTopLevelItem(dep_item)

        installed = dependencies.get('installed', {})
        for package, version in installed.items():
            child = QTreeWidgetItem([package, "✅", version])
            dep_item.addChild(child)

        missing = dependencies.get('missing', [])
        for package in missing:
            child = QTreeWidgetItem([package, "❌", "未安装"])
            dep_item.addChild(child)

        # GPU配置
        gpu_config = result.get('gpu_config', {})
        gpu_status = "✅" if gpu_config.get('gpu_available') else "❌"
        gpu_item = QTreeWidgetItem(["🎮 GPU配置", gpu_status, ""])
        self.details_tree.addTopLevelItem(gpu_item)

        # 展开所有项目
        self.details_tree.expandAll()

    def _update_solutions(self, result: dict):
        """更新解决方案"""
        # 清空解决方案区域
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 添加说明文本
        if not result.get('issues'):
            info_label = QLabel("✅ 系统配置良好，无需额外操作。")
            info_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
            layout.addWidget(info_label)
        else:
            info_label = QLabel("🔧 检测到配置问题，请点击下方按钮进行修复：")
            info_label.setStyleSheet("color: #333; font-weight: bold; font-size: 14px;")
            layout.addWidget(info_label)

            # 根据问题类型添加相应的解决按钮
            self._add_solution_buttons(layout, result)

        layout.addStretch()

        # 替换解决方案标签页的内容
        self.tab_widget.removeTab(2)  # 移除旧的解决方案标签页
        self.tab_widget.insertTab(2, widget, "💡 解决方案")

    def _add_solution_buttons(self, layout, result):
        """添加解决方案按钮"""
        issues = result.get('issues', [])
        dependencies = result.get('dependencies', {})
        models = result.get('models', {})
        ffmpeg = result.get('ffmpeg', {})
        gpu_config = result.get('gpu_config', {})

        # 依赖包问题
        if dependencies.get('missing'):
            missing_deps = dependencies['missing']
            group = QGroupBox(f"📦 缺少依赖包 ({len(missing_deps)}个)")
            group_layout = QVBoxLayout(group)

            deps_label = QLabel(f"缺少: {', '.join(missing_deps)}")
            deps_label.setWordWrap(True)
            group_layout.addWidget(deps_label)

            install_deps_btn = QPushButton("🔧 一键安装依赖包")
            install_deps_btn.clicked.connect(lambda: self._install_dependencies(missing_deps))
            install_deps_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            group_layout.addWidget(install_deps_btn)
            layout.addWidget(group)

        # 模型文件问题
        if models.get('missing'):
            missing_models = models['missing']
            group = QGroupBox(f"🤖 缺少模型文件 ({len(missing_models)}个)")
            group_layout = QVBoxLayout(group)

            models_label = QLabel(f"缺少: {', '.join(missing_models)}")
            models_label.setWordWrap(True)
            group_layout.addWidget(models_label)

            download_models_btn = QPushButton("📥 一键下载模型文件")
            download_models_btn.clicked.connect(self._download_models)
            download_models_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            group_layout.addWidget(download_models_btn)
            layout.addWidget(group)

        # FFmpeg问题
        if not ffmpeg.get('available'):
            group = QGroupBox("🎬 FFmpeg未安装")
            group_layout = QVBoxLayout(group)

            ffmpeg_label = QLabel("FFmpeg用于视频处理功能，建议安装以获得完整功能。")
            ffmpeg_label.setWordWrap(True)
            group_layout.addWidget(ffmpeg_label)

            button_layout = QHBoxLayout()

            download_ffmpeg_btn = QPushButton("📥 自动下载FFmpeg")
            download_ffmpeg_btn.clicked.connect(self._download_ffmpeg)
            download_ffmpeg_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
            button_layout.addWidget(download_ffmpeg_btn)

            manual_ffmpeg_btn = QPushButton("🌐 手动下载FFmpeg")
            manual_ffmpeg_btn.clicked.connect(self._open_ffmpeg_download)
            manual_ffmpeg_btn.setStyleSheet("""
                QPushButton {
                    background-color: #9C27B0;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #7B1FA2;
                }
            """)
            button_layout.addWidget(manual_ffmpeg_btn)

            group_layout.addLayout(button_layout)
            layout.addWidget(group)

        # GPU配置问题
        if not gpu_config.get('gpu_available') and any('GPU' in issue or 'CUDA' in issue for issue in issues):
            group = QGroupBox("🎮 GPU加速配置问题")
            group_layout = QVBoxLayout(group)

            gpu_label = QLabel("检测到GPU但无法正常使用，可能是驱动或配置问题。")
            gpu_label.setWordWrap(True)
            group_layout.addWidget(gpu_label)

            button_layout = QHBoxLayout()

            fix_gpu_btn = QPushButton("🔧 自动修复GPU配置")
            fix_gpu_btn.clicked.connect(self._fix_gpu_config)
            fix_gpu_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #D32F2F;
                }
            """)
            button_layout.addWidget(fix_gpu_btn)

            gpu_guide_btn = QPushButton("📖 GPU配置指南")
            gpu_guide_btn.clicked.connect(self._show_gpu_guide)
            gpu_guide_btn.setStyleSheet("""
                QPushButton {
                    background-color: #607D8B;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #455A64;
                }
            """)
            button_layout.addWidget(gpu_guide_btn)

            group_layout.addLayout(button_layout)
            layout.addWidget(group)

        # ONNX Runtime版本问题（最常见的GPU问题）
        if any('onnx' in issue.lower() or 'version' in issue.lower() for issue in issues):
            group = QGroupBox("⚡ ONNX Runtime版本问题")
            group_layout = QVBoxLayout(group)

            onnx_label = QLabel("检测到ONNX Runtime版本兼容性问题，这是GPU无法使用的最常见原因。")
            onnx_label.setWordWrap(True)
            group_layout.addWidget(onnx_label)

            quick_fix_btn = QPushButton("⚡ 一键修复ONNX Runtime版本")
            quick_fix_btn.clicked.connect(self._quick_fix_onnx)
            quick_fix_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E91E63;
                    color: white;
                    border: none;
                    padding: 12px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #C2185B;
                }
            """)
            group_layout.addWidget(quick_fix_btn)
            layout.addWidget(group)

    def _create_cuda_tab(self):
        """创建CUDA诊断标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # CUDA诊断按钮
        cuda_button_layout = QHBoxLayout()

        self.cuda_diagnose_button = QPushButton("🔍 运行CUDA诊断")
        self.cuda_diagnose_button.clicked.connect(self._run_cuda_diagnosis)
        cuda_button_layout.addWidget(self.cuda_diagnose_button)

        self.cuda_fix_button = QPushButton("🔧 自动修复GPU问题")
        self.cuda_fix_button.clicked.connect(self._run_gpu_fix)
        self.cuda_fix_button.setEnabled(False)
        cuda_button_layout.addWidget(self.cuda_fix_button)

        cuda_button_layout.addStretch()
        layout.addLayout(cuda_button_layout)

        # CUDA诊断结果
        self.cuda_result_text = QTextEdit()
        self.cuda_result_text.setPlainText("点击'运行CUDA诊断'按钮开始检测...")
        layout.addWidget(self.cuda_result_text)

        return widget

    def _run_cuda_diagnosis(self):
        """运行CUDA诊断"""
        self.cuda_diagnose_button.setEnabled(False)
        self.cuda_result_text.setPlainText("正在运行CUDA诊断，请稍候...")

        # 使用线程避免界面卡死
        from PyQt5.QtCore import QThread, pyqtSignal

        class CUDADiagnosisWorker(QThread):
            diagnosis_completed = pyqtSignal(dict)
            diagnosis_failed = pyqtSignal(str)

            def run(self):
                try:
                    # 使用简化的CUDA检查避免卡死
                    from utils.simple_cuda_check import quick_cuda_check, format_simple_report

                    result = quick_cuda_check()
                    result['formatted_report'] = format_simple_report(result)
                    self.diagnosis_completed.emit(result)

                except Exception as e:
                    self.diagnosis_failed.emit(str(e))

        self.cuda_worker = CUDADiagnosisWorker()
        self.cuda_worker.diagnosis_completed.connect(self._on_cuda_diagnosis_completed)
        self.cuda_worker.diagnosis_failed.connect(self._on_cuda_diagnosis_failed)
        self.cuda_worker.start()

    def _on_cuda_diagnosis_completed(self, result):
        """CUDA诊断完成"""
        try:
            # 使用预格式化的报告
            if 'formatted_report' in result:
                diagnosis_text = result['formatted_report']
            else:
                diagnosis_text = self._format_cuda_diagnosis(result)

            self.cuda_result_text.setPlainText(diagnosis_text)

            # 如果有问题，启用修复按钮
            if result.get('main_issue') or result.get('issues'):
                self.cuda_fix_button.setEnabled(True)

        except Exception as e:
            self.cuda_result_text.setPlainText(f"格式化诊断结果失败: {e}")

        finally:
            self.cuda_diagnose_button.setEnabled(True)

    def _on_cuda_diagnosis_failed(self, error_msg):
        """CUDA诊断失败"""
        self.cuda_result_text.setPlainText(f"CUDA诊断失败: {error_msg}")
        self.cuda_diagnose_button.setEnabled(True)

    def _format_cuda_diagnosis(self, result: dict) -> str:
        """格式化CUDA诊断结果"""
        text = "🔍 CUDA配置诊断报告\n"
        text += "=" * 50 + "\n\n"

        # ONNX Runtime信息
        onnx_info = result.get('onnxruntime_version', {})
        text += "📦 ONNX Runtime:\n"
        if onnx_info.get('installed', True):
            text += f"   版本: {onnx_info.get('version', 'Unknown')}\n"
            text += f"   GPU包: {'是' if onnx_info.get('has_gpu_package') else '否'}\n"
            text += f"   CPU包: {'是' if onnx_info.get('has_cpu_package') else '否'}\n"
            text += f"   CUDA提供者: {'可用' if onnx_info.get('has_cuda_provider') else '不可用'}\n"
        else:
            text += "   ❌ 未安装\n"

        # CUDA安装信息
        cuda_info = result.get('cuda_installation', {})
        text += "\n🚀 CUDA安装:\n"
        text += f"   NVCC: {'可用' if cuda_info.get('nvcc_available') else '不可用'}\n"
        text += f"   NVIDIA-SMI: {'可用' if cuda_info.get('nvidia_smi_available') else '不可用'}\n"
        if cuda_info.get('cuda_version'):
            text += f"   CUDA版本: {cuda_info['cuda_version']}\n"
        if cuda_info.get('driver_version'):
            text += f"   驱动版本: {cuda_info['driver_version']}\n"

        # GPU信息
        if cuda_info.get('gpu_info'):
            text += "\n🎮 GPU信息:\n"
            for i, gpu in enumerate(cuda_info['gpu_info']):
                text += f"   GPU {i}: {gpu['name']} ({gpu['memory_mb']}MB)\n"

        # CUDA库信息
        libs_info = result.get('cuda_runtime_libs', {})
        text += "\n📚 CUDA库:\n"
        text += f"   运行时库: {'找到' if libs_info.get('cuda_runtime_found') else '未找到'}\n"
        text += f"   CUBLAS: {'找到' if libs_info.get('cublas_found') else '未找到'}\n"
        text += f"   CUDNN: {'找到' if libs_info.get('cudnn_found') else '未找到'}\n"

        # 提供者测试结果
        provider_test = result.get('onnx_cuda_provider', {})
        text += "\n🧪 CUDA提供者测试:\n"
        if provider_test.get('success'):
            text += "   ✅ 测试通过\n"
            text += f"   使用CUDA: {'是' if provider_test.get('cuda_used') else '否'}\n"
        else:
            text += "   ❌ 测试失败\n"
            if provider_test.get('error'):
                text += f"   错误: {provider_test['error']}\n"

        # 问题和建议
        if result.get('issues'):
            text += f"\n❌ 发现问题 ({len(result['issues'])}个):\n"
            for i, issue in enumerate(result['issues'], 1):
                text += f"   {i}. {issue}\n"

        if result.get('recommendations'):
            text += f"\n💡 建议操作 ({len(result['recommendations'])}个):\n"
            for i, rec in enumerate(result['recommendations'], 1):
                text += f"   {i}. {rec}\n"

        return text

    def _run_gpu_fix(self):
        """运行GPU问题修复"""
        from PyQt5.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "确认修复",
            "这将自动修复检测到的GPU配置问题。\n\n"
            "操作包括：\n"
            "• 卸载并重新安装ONNX Runtime GPU版本\n"
            "• 安装兼容的CUDA库版本\n\n"
            "是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.cuda_fix_button.setEnabled(False)
            self.cuda_result_text.append("\n" + "=" * 50)
            self.cuda_result_text.append("🔧 开始自动修复GPU问题...")

            try:
                # 这里可以调用修复脚本
                import subprocess
                import sys

                script_path = project_root / "scripts" / "fix_gpu_simple.py"
                result = subprocess.run([sys.executable, str(script_path)],
                                      capture_output=True, text=True, timeout=600)

                if result.returncode == 0:
                    self.cuda_result_text.append("✅ GPU问题修复完成")
                    self.cuda_result_text.append("建议重启应用程序以应用更改")
                else:
                    self.cuda_result_text.append("❌ GPU问题修复失败")
                    if result.stderr:
                        self.cuda_result_text.append(f"错误: {result.stderr}")

            except Exception as e:
                self.cuda_result_text.append(f"❌ 修复过程出错: {e}")

            finally:
                self.cuda_fix_button.setEnabled(True)

    def _install_dependencies(self, missing_deps):
        """安装依赖包"""
        from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextEdit, QPushButton, QProgressBar, QLabel
        from PyQt5.QtCore import QThread, pyqtSignal, Qt
        import subprocess
        import sys

        reply = QMessageBox.question(
            self,
            "安装依赖包",
            f"将要安装以下依赖包：\n{', '.join(missing_deps)}\n\n"
            "这可能需要几分钟时间，是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            # 创建安装进度对话框
            install_dialog = QDialog(self)
            install_dialog.setWindowTitle("安装依赖包")
            install_dialog.setFixedSize(500, 350)
            install_dialog.setWindowModality(Qt.WindowModal)

            layout = QVBoxLayout(install_dialog)

            # 状态标签
            status_label = QLabel("准备安装依赖包...")
            status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
            layout.addWidget(status_label)

            # 进度条
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(0)
            layout.addWidget(progress_bar)

            # 安装日志
            log_text = QTextEdit()
            log_text.setReadOnly(True)
            log_text.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f8f8;
                    border: 1px solid #ddd;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 12px;
                }
            """)
            layout.addWidget(log_text)

            # 关闭按钮
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(install_dialog.close)
            close_btn.setEnabled(False)
            layout.addWidget(close_btn)

            install_dialog.show()

            class InstallWorker(QThread):
                progress_updated = pyqtSignal(str, int)
                log_updated = pyqtSignal(str)
                finished = pyqtSignal(bool, str)

                def __init__(self, deps):
                    super().__init__()
                    self.deps = deps

                def run(self):
                    try:
                        self.progress_updated.emit("开始安装依赖包...", 10)
                        self.log_updated.emit("📦 开始安装Python依赖包...")
                        self.log_updated.emit(f"需要安装: {', '.join(self.deps)}")

                        # 检查是否有虚拟环境
                        venv_dir = project_root / "venv"
                        if venv_dir.exists():
                            pip_exe = venv_dir / "Scripts" / "pip.exe"
                            self.log_updated.emit(f"使用虚拟环境: {venv_dir}")
                        else:
                            pip_exe = "pip"
                            self.log_updated.emit("使用系统Python环境")

                        # 安装缺少的包
                        self.progress_updated.emit("正在安装缺少的包...", 30)

                        for i, package in enumerate(self.deps):
                            progress = 30 + (i + 1) * 50 // len(self.deps)
                            self.progress_updated.emit(f"安装 {package}...", progress)
                            self.log_updated.emit(f"\n安装 {package}...")

                            result = subprocess.run([
                                str(pip_exe), 'install', package
                            ], capture_output=True, text=True, timeout=300)

                            if result.returncode == 0:
                                self.log_updated.emit(f"✅ {package} 安装成功")
                            else:
                                self.log_updated.emit(f"❌ {package} 安装失败: {result.stderr}")

                        # 最后尝试安装requirements.txt
                        self.progress_updated.emit("安装requirements.txt...", 80)
                        self.log_updated.emit("\n执行命令: pip install -r requirements.txt")

                        result = subprocess.run([
                            str(pip_exe), 'install', '-r', 'requirements.txt'
                        ], capture_output=True, text=True, timeout=300)

                        self.progress_updated.emit("安装完成，验证结果...", 80)

                        if result.returncode == 0:
                            self.log_updated.emit("✅ 依赖包安装成功！")
                            self.log_updated.emit(result.stdout)
                            self.progress_updated.emit("安装成功！", 100)
                            self.finished.emit(True, "依赖包安装成功！")
                        else:
                            self.log_updated.emit("❌ 安装失败")
                            self.log_updated.emit(result.stderr)
                            self.finished.emit(False, f"安装失败：{result.stderr}")
                    except Exception as e:
                        self.log_updated.emit(f"❌ 安装过程出错：{str(e)}")
                        self.finished.emit(False, f"安装过程出错：{str(e)}")

            def on_progress_updated(message, progress):
                status_label.setText(message)
                progress_bar.setValue(progress)

            def on_log_updated(message):
                log_text.append(message)
                scrollbar = log_text.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())

            def on_install_finished(success, message):
                close_btn.setEnabled(True)
                if success:
                    status_label.setText("✅ 安装完成！")
                    # 重新检测
                    self._start_check()
                else:
                    status_label.setText("❌ 安装失败")

            worker = InstallWorker(missing_deps)
            worker.progress_updated.connect(on_progress_updated)
            worker.log_updated.connect(on_log_updated)
            worker.finished.connect(on_install_finished)
            worker.start()

    def _download_models(self):
        """下载模型文件"""
        from PyQt5.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "下载模型文件",
            "将要下载AI换脸所需的模型文件。\n\n"
            "文件较大（约1-2GB），下载可能需要较长时间，\n"
            "建议在网络良好时进行。是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            try:
                from gui.download_manager import show_download_manager
                success = show_download_manager()
                if success:
                    QMessageBox.information(self, "下载完成", "模型文件下载成功！")
                    self._start_check()  # 重新检测
            except Exception as e:
                QMessageBox.critical(self, "下载失败", f"启动下载管理器失败：{str(e)}")

    def _download_ffmpeg(self):
        """下载FFmpeg"""
        from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextEdit, QPushButton, QProgressBar, QLabel
        from PyQt5.QtCore import QThread, pyqtSignal, Qt
        import subprocess
        import sys

        reply = QMessageBox.question(
            self,
            "下载FFmpeg",
            "将要自动下载并配置FFmpeg。\n\n"
            "FFmpeg用于视频处理功能，文件较大（约100MB），\n"
            "下载时间取决于网络速度。是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            # 创建下载进度对话框
            download_dialog = QDialog(self)
            download_dialog.setWindowTitle("下载FFmpeg")
            download_dialog.setFixedSize(500, 350)
            download_dialog.setWindowModality(Qt.WindowModal)

            layout = QVBoxLayout(download_dialog)

            # 状态标签
            status_label = QLabel("准备下载FFmpeg...")
            status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
            layout.addWidget(status_label)

            # 进度条
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(0)
            layout.addWidget(progress_bar)

            # 下载日志
            log_text = QTextEdit()
            log_text.setReadOnly(True)
            log_text.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f8f8;
                    border: 1px solid #ddd;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 12px;
                }
            """)
            layout.addWidget(log_text)

            # 关闭按钮
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(download_dialog.close)
            close_btn.setEnabled(False)
            layout.addWidget(close_btn)

            download_dialog.show()

            class FFmpegWorker(QThread):
                progress_updated = pyqtSignal(str, int)
                log_updated = pyqtSignal(str)
                finished = pyqtSignal(bool, str)

                def run(self):
                    try:
                        self.progress_updated.emit("开始下载FFmpeg...", 10)
                        self.log_updated.emit("🎬 开始下载FFmpeg...")
                        self.log_updated.emit("FFmpeg是视频处理的核心工具")

                        # 检查是否存在下载脚本
                        import os
                        script_path = "download_ffmpeg.py"
                        if not os.path.exists(script_path):
                            self.log_updated.emit("❌ 下载脚本不存在，尝试手动下载...")
                            self.progress_updated.emit("脚本不存在，提供手动下载指引...", 50)
                            self.log_updated.emit("\n手动下载步骤：")
                            self.log_updated.emit("1. 访问 https://ffmpeg.org/download.html")
                            self.log_updated.emit("2. 下载Windows版本的FFmpeg")
                            self.log_updated.emit("3. 解压到项目的ffmpeg文件夹中")
                            self.log_updated.emit("4. 确保ffmpeg.exe在ffmpeg文件夹内")
                            self.finished.emit(False, "请手动下载FFmpeg")
                            return

                        self.progress_updated.emit("正在执行下载脚本...", 30)
                        self.log_updated.emit("\n执行下载脚本...")

                        # 运行FFmpeg下载脚本
                        result = subprocess.run([
                            sys.executable, script_path
                        ], capture_output=True, text=True, timeout=600)

                        self.progress_updated.emit("下载完成，验证安装...", 80)

                        if result.returncode == 0:
                            self.log_updated.emit("✅ FFmpeg下载安装成功！")
                            self.log_updated.emit(result.stdout)
                            self.progress_updated.emit("安装成功！", 100)
                            self.finished.emit(True, "FFmpeg下载安装成功！")
                        else:
                            self.log_updated.emit("❌ 下载失败")
                            self.log_updated.emit(result.stderr)
                            self.log_updated.emit("\n建议手动下载FFmpeg")
                            self.finished.emit(False, f"下载失败：{result.stderr}")
                    except Exception as e:
                        self.log_updated.emit(f"❌ 下载过程出错：{str(e)}")
                        self.finished.emit(False, f"下载过程出错：{str(e)}")

            def on_progress_updated(message, progress):
                status_label.setText(message)
                progress_bar.setValue(progress)

            def on_log_updated(message):
                log_text.append(message)
                scrollbar = log_text.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())

            def on_ffmpeg_finished(success, message):
                close_btn.setEnabled(True)
                if success:
                    status_label.setText("✅ 下载完成！")
                    self._start_check()
                else:
                    status_label.setText("❌ 下载失败")

            worker = FFmpegWorker()
            worker.progress_updated.connect(on_progress_updated)
            worker.log_updated.connect(on_log_updated)
            worker.finished.connect(on_ffmpeg_finished)
            worker.start()

    def _open_ffmpeg_download(self):
        """打开FFmpeg官方下载页面"""
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtCore import QUrl
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "手动下载FFmpeg",
            "即将打开FFmpeg官方下载页面。\n\n"
            "请下载适合您系统的版本，并将ffmpeg.exe\n"
            "放置在项目的ffmpeg文件夹中。"
        )

        QDesktopServices.openUrl(QUrl("https://ffmpeg.org/download.html"))

    def _fix_gpu_config(self):
        """修复GPU配置"""
        from PyQt5.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "修复GPU配置",
            "将要自动修复GPU配置问题。\n\n"
            "操作包括：\n"
            "• 检测并修复ONNX Runtime版本问题\n"
            "• 重新配置CUDA提供者\n"
            "• 测试GPU功能\n\n"
            "是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            # 切换到CUDA诊断标签页并运行修复
            self.tab_widget.setCurrentIndex(3)  # CUDA诊断标签页
            self._run_gpu_fix()

    def _show_gpu_guide(self):
        """显示GPU配置指南"""
        from PyQt5.QtWidgets import QMessageBox

        guide_text = """
🎮 GPU配置指南

1. 检查硬件：
   • 确保您的显卡支持CUDA（NVIDIA显卡）
   • 显卡驱动程序是最新版本

2. 安装CUDA：
   • 访问NVIDIA官网下载CUDA Toolkit
   • 选择与您的显卡兼容的版本

3. 配置环境：
   • 确保CUDA_PATH环境变量正确设置
   • 重启计算机使环境变量生效

4. 验证安装：
   • 在命令行运行 nvidia-smi 检查GPU状态
   • 在命令行运行 nvcc --version 检查CUDA版本

如果仍有问题，建议使用CPU模式或联系技术支持。
        """

        QMessageBox.information(self, "GPU配置指南", guide_text)

    def _quick_fix_onnx(self):
        """一键修复ONNX Runtime版本"""
        from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextEdit, QPushButton, QProgressBar, QLabel
        from PyQt5.QtCore import QThread, pyqtSignal, Qt
        import subprocess
        import sys

        reply = QMessageBox.question(
            self,
            "修复ONNX Runtime版本",
            "将要自动修复ONNX Runtime版本兼容性问题。\n\n"
            "操作包括：\n"
            "• 卸载当前版本的ONNX Runtime\n"
            "• 尝试安装多个兼容版本\n"
            "• 验证GPU功能\n\n"
            "这是解决GPU无法使用问题的最有效方法。\n"
            "是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            # 创建修复进度对话框
            self.fix_dialog = QDialog(self)
            self.fix_dialog.setWindowTitle("修复ONNX Runtime")
            self.fix_dialog.setFixedSize(600, 400)
            self.fix_dialog.setWindowModality(Qt.WindowModal)

            layout = QVBoxLayout(self.fix_dialog)

            # 状态标签
            self.fix_status_label = QLabel("准备开始修复...")
            self.fix_status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
            layout.addWidget(self.fix_status_label)

            # 进度条
            self.fix_progress = QProgressBar()
            self.fix_progress.setRange(0, 100)
            self.fix_progress.setValue(0)
            layout.addWidget(self.fix_progress)

            # 详细日志
            self.fix_log = QTextEdit()
            self.fix_log.setReadOnly(True)
            self.fix_log.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f8f8;
                    border: 1px solid #ddd;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 12px;
                }
            """)
            layout.addWidget(self.fix_log)

            # 关闭按钮
            self.fix_close_btn = QPushButton("关闭")
            self.fix_close_btn.clicked.connect(self.fix_dialog.close)
            self.fix_close_btn.setEnabled(False)
            layout.addWidget(self.fix_close_btn)

            self.fix_dialog.show()

            # 启动修复工作线程
            class ONNXFixWorker(QThread):
                progress_updated = pyqtSignal(str, int)  # 状态消息, 进度
                log_updated = pyqtSignal(str)  # 日志消息
                finished = pyqtSignal(bool, str)  # 成功/失败, 最终消息

                def run(self):
                    try:
                        self.fix_onnx_runtime()
                    except Exception as e:
                        self.finished.emit(False, f"修复过程出错：{str(e)}")

                def fix_onnx_runtime(self):
                    """修复ONNX Runtime版本"""
                    self.progress_updated.emit("开始修复ONNX Runtime版本...", 10)
                    self.log_updated.emit("🔧 开始修复ONNX Runtime版本问题...")

                    # 步骤1: 卸载现有版本
                    self.progress_updated.emit("卸载现有版本...", 20)
                    self.log_updated.emit("\n📋 步骤1: 卸载现有ONNX Runtime版本")

                    uninstall_commands = [
                        ('onnxruntime', [sys.executable, '-m', 'pip', 'uninstall', 'onnxruntime', '-y']),
                        ('onnxruntime-gpu', [sys.executable, '-m', 'pip', 'uninstall', 'onnxruntime-gpu', '-y']),
                        ('onnxruntime-directml', [sys.executable, '-m', 'pip', 'uninstall', 'onnxruntime-directml', '-y'])
                    ]

                    for package_name, cmd in uninstall_commands:
                        self.log_updated.emit(f"卸载 {package_name}...")
                        try:
                            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                            if result.returncode == 0:
                                self.log_updated.emit(f"✅ {package_name} 卸载成功")
                            else:
                                self.log_updated.emit(f"⚠️ {package_name} 可能未安装")
                        except Exception as e:
                            self.log_updated.emit(f"❌ 卸载 {package_name} 失败: {e}")

                    # 步骤2: 尝试安装兼容版本
                    self.progress_updated.emit("安装兼容版本...", 40)
                    self.log_updated.emit("\n📋 步骤2: 安装兼容版本的ONNX Runtime GPU")

                    versions_to_try = [
                        "1.18.1",  # 支持CUDA 12.x的较新版本
                        "1.17.3",  # 稳定版本
                        "1.16.3",  # 之前尝试的版本
                        None       # 最新版本
                    ]

                    success = False
                    for i, target_version in enumerate(versions_to_try):
                        progress = 40 + (i + 1) * 15  # 40-100之间分配进度

                        if target_version:
                            install_cmd = [sys.executable, '-m', 'pip', 'install', f'onnxruntime-gpu=={target_version}']
                            version_text = f"onnxruntime-gpu=={target_version}"
                        else:
                            install_cmd = [sys.executable, '-m', 'pip', 'install', 'onnxruntime-gpu']
                            version_text = "最新版本的onnxruntime-gpu"

                        self.progress_updated.emit(f"尝试安装 {version_text}...", progress)
                        self.log_updated.emit(f"尝试安装 {version_text}...")

                        try:
                            result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=300)
                            if result.returncode == 0:
                                self.log_updated.emit(f"✅ {version_text} 安装成功")

                                # 测试这个版本
                                if self.test_onnx_version():
                                    self.log_updated.emit(f"✅ {version_text} 测试通过")
                                    success = True
                                    break
                                else:
                                    self.log_updated.emit(f"⚠️ {version_text} 安装成功但测试失败，尝试下一个版本...")
                            else:
                                self.log_updated.emit(f"❌ {version_text} 安装失败")
                        except Exception as e:
                            self.log_updated.emit(f"❌ 安装 {version_text} 过程出错: {e}")

                    if not success:
                        self.finished.emit(False, "所有版本都安装失败")
                        return

                    # 步骤3: 验证安装
                    self.progress_updated.emit("验证安装结果...", 90)
                    self.log_updated.emit("\n📋 步骤3: 验证安装结果")

                    try:
                        import onnxruntime as ort
                        version = ort.__version__
                        providers = ort.get_available_providers()

                        self.log_updated.emit(f"✅ ONNX Runtime版本: {version}")
                        self.log_updated.emit(f"✅ 可用提供者: {providers}")

                        if 'CUDAExecutionProvider' in providers:
                            self.log_updated.emit("✅ CUDA提供者可用")
                            self.progress_updated.emit("修复完成！", 100)
                            self.finished.emit(True, "ONNX Runtime版本修复成功！\n\nGPU加速现在应该可以正常工作了。")
                        else:
                            self.log_updated.emit("⚠️ CUDA提供者不可用")
                            self.finished.emit(False, "修复部分成功，但CUDA提供者仍不可用")
                    except Exception as e:
                        self.log_updated.emit(f"❌ 验证失败: {e}")
                        self.finished.emit(False, f"验证过程出错: {e}")

                def test_onnx_version(self):
                    """测试当前ONNX Runtime版本是否工作"""
                    try:
                        # 重新加载模块
                        if 'onnxruntime' in sys.modules:
                            del sys.modules['onnxruntime']

                        import onnxruntime as ort
                        providers = ort.get_available_providers()
                        return 'CUDAExecutionProvider' in providers
                    except Exception:
                        return False

            def on_progress_updated(message, progress):
                self.fix_status_label.setText(message)
                self.fix_progress.setValue(progress)

            def on_log_updated(message):
                self.fix_log.append(message)
                # 自动滚动到底部
                scrollbar = self.fix_log.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())

            def on_fix_finished(success, message):
                self.fix_close_btn.setEnabled(True)
                if success:
                    self.fix_status_label.setText("✅ 修复完成！")
                    self.fix_log.append(f"\n🎉 {message}")
                    # 重新检测
                    self._start_check()
                else:
                    self.fix_status_label.setText("❌ 修复失败")
                    self.fix_log.append(f"\n❌ {message}")

            self.fix_worker = ONNXFixWorker()
            self.fix_worker.progress_updated.connect(on_progress_updated)
            self.fix_worker.log_updated.connect(on_log_updated)
            self.fix_worker.finished.connect(on_fix_finished)
            self.fix_worker.start()

def show_startup_checker(parent=None) -> bool:
    """显示启动配置检测对话框"""
    dialog = StartupCheckerDialog(parent)
    result = dialog.exec_()
    return result == QDialog.Accepted

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置应用信息
    app.setApplicationName("AI换脸工具配置检测")
    app.setApplicationVersion("1.0")

    success = show_startup_checker()
    print(f"检测结果: {'继续启动' if success else '用户取消'}")

    sys.exit(0)
