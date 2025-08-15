"""
GPU配置向导 - 傻瓜式GPU配置界面
"""

import sys
import subprocess
import platform
from pathlib import Path
from PyQt5.QtWidgets import (QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QTextEdit, QProgressBar, 
                            QRadioButton, QButtonGroup, QMessageBox, QCheckBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPixmap


class GPUDetectionPage(QWizardPage):
    """GPU检测页面"""
    
    def __init__(self, gpu_config):
        super().__init__()
        self.gpu_config = gpu_config
        self.setTitle("🔍 GPU环境检测")
        self.setSubTitle("正在检测您的GPU硬件和驱动环境...")
        
        layout = QVBoxLayout()
        
        # 检测结果显示
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(200)
        layout.addWidget(self.result_text)
        
        # 重新检测按钮
        self.redetect_btn = QPushButton("🔄 重新检测")
        self.redetect_btn.clicked.connect(self.detect_gpu)
        layout.addWidget(self.redetect_btn)
        
        self.setLayout(layout)
        
        # 自动开始检测
        self.detect_gpu()
    
    def detect_gpu(self):
        """检测GPU环境"""
        self.result_text.clear()
        self.result_text.append("🔍 正在检测GPU环境...\n")

        try:
            # 导入GPU检测器
            import sys
            import os

            # 获取项目根目录
            current_dir = Path(__file__).parent
            project_root = current_dir.parent

            # 添加项目根目录到Python路径
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            # 导入GPU检测器
            from utils.gpu_detector import GPUDetector

            detector = GPUDetector()
            gpu_result = detector.detect_all()

            # 显示检测结果
            self._display_detection_result(gpu_result)

            # 更新向导数据
            self.wizard().gpu_detection_result = gpu_result

        except ImportError as e:
            self.result_text.append(f"❌ 导入失败: {e}")
            self.result_text.append(f"📁 当前路径: {Path(__file__).parent}")
            self.result_text.append(f"📁 项目根目录: {Path(__file__).parent.parent}")
        except Exception as e:
            self.result_text.append(f"❌ 检测失败: {e}")
            import traceback
            self.result_text.append(f"📋 详细错误: {traceback.format_exc()}")
    
    def _display_detection_result(self, result):
        """显示检测结果"""
        self.result_text.clear()
        
        # 系统信息
        self.result_text.append(f"💻 操作系统: {result['system']}")
        
        # NVIDIA GPU
        nvidia = result['nvidia_gpu']
        self.result_text.append(f"\n🎮 NVIDIA GPU:")
        if nvidia.get('available'):
            self.result_text.append(f"   ✅ 状态: 可用 ({nvidia['count']}个GPU)")
            for i, gpu in enumerate(nvidia['gpus']):
                self.result_text.append(f"   📊 GPU {i+1}: {gpu['name']} ({gpu['memory_mb']}MB)")
        else:
            self.result_text.append(f"   ❌ 状态: 不可用 ({nvidia.get('error', '未知错误')})")
        
        # CUDA
        cuda = result['cuda']
        self.result_text.append(f"\n🚀 CUDA:")
        if cuda.get('available'):
            self.result_text.append(f"   ✅ 状态: 可用")
            self.result_text.append(f"   📋 版本: {cuda['version_info']}")
        else:
            self.result_text.append(f"   ❌ 状态: 不可用 ({cuda.get('error', '未知错误')})")
        
        # ONNX Runtime
        onnx = result['onnx_providers']
        self.result_text.append(f"\n🧠 ONNX Runtime:")
        if onnx.get('available'):
            self.result_text.append(f"   ✅ 状态: 可用 (版本 {onnx['onnxruntime_version']})")
            self.result_text.append(f"   📋 可用提供者:")
            for provider in onnx['providers']:
                details = onnx['details'].get(provider, {})
                status = "✅" if details.get('available', True) else "❌"
                desc = details.get('description', provider)
                self.result_text.append(f"       {status} {provider}: {desc}")
        else:
            self.result_text.append(f"   ❌ 状态: 不可用 ({onnx.get('error', '未知错误')})")
        
        # 推荐配置
        recommended = result.get('recommended_config', {})
        self.result_text.append(f"\n🎯 推荐配置:")
        self.result_text.append(f"   📋 类型: {recommended.get('description', '未知')}")
        self.result_text.append(f"   🚀 提供者: {recommended.get('provider', '未知')}")
        self.result_text.append(f"   📊 性能等级: {recommended.get('performance', '未知')}")
        self.result_text.append(f"   💡 原因: {recommended.get('reason', '未知')}")


class GPUConfigSelectionPage(QWizardPage):
    """GPU配置选择页面"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("⚙️ 选择配置方案")
        self.setSubTitle("根据检测结果，选择最适合您的GPU配置方案")
        
        layout = QVBoxLayout()
        
        # 配置选项
        self.config_group = QButtonGroup()
        
        # NVIDIA CUDA选项
        self.cuda_radio = QRadioButton("🚀 NVIDIA CUDA GPU加速 (推荐)")
        self.cuda_radio.setToolTip("适用于NVIDIA显卡，性能最佳")
        self.config_group.addButton(self.cuda_radio, 0)
        layout.addWidget(self.cuda_radio)
        
        # DirectML选项
        self.directml_radio = QRadioButton("⚡ DirectML GPU加速 (通用)")
        self.directml_radio.setToolTip("适用于AMD/Intel/NVIDIA显卡，兼容性好")
        self.config_group.addButton(self.directml_radio, 1)
        layout.addWidget(self.directml_radio)
        
        # CPU选项
        self.cpu_radio = QRadioButton("💻 CPU模式 (兼容性最佳)")
        self.cpu_radio.setToolTip("适用于所有系统，性能较慢但最稳定")
        self.config_group.addButton(self.cpu_radio, 2)
        layout.addWidget(self.cpu_radio)
        
        # 自动安装选项
        self.auto_install_checkbox = QCheckBox("🔧 自动安装缺失的依赖")
        self.auto_install_checkbox.setChecked(True)
        layout.addWidget(self.auto_install_checkbox)
        
        self.setLayout(layout)
    
    def initializePage(self):
        """页面初始化时根据检测结果设置默认选项"""
        gpu_result = self.wizard().gpu_detection_result
        recommended = gpu_result.get('recommended_config', {})
        config_type = recommended.get('type', 'cpu_only')
        
        # 根据推荐配置设置默认选项
        if config_type == 'cuda_gpu':
            self.cuda_radio.setChecked(True)
        elif config_type == 'directml_gpu':
            self.directml_radio.setChecked(True)
        else:
            self.cpu_radio.setChecked(True)
        
        # 根据检测结果启用/禁用选项
        nvidia_available = gpu_result.get('nvidia_gpu', {}).get('available', False)
        cuda_available = gpu_result.get('cuda', {}).get('available', False)
        
        # 如果没有NVIDIA GPU或CUDA，禁用CUDA选项
        if not nvidia_available or not cuda_available:
            self.cuda_radio.setEnabled(False)
            self.cuda_radio.setToolTip("需要NVIDIA GPU和CUDA支持")
        
        # Windows系统才支持DirectML
        if platform.system() != "Windows":
            self.directml_radio.setEnabled(False)
            self.directml_radio.setToolTip("仅支持Windows系统")


class GPUInstallationPage(QWizardPage):
    """GPU安装页面"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("📦 安装GPU支持")
        self.setSubTitle("正在安装所需的GPU加速组件...")
        
        layout = QVBoxLayout()
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 不确定进度
        layout.addWidget(self.progress_bar)
        
        # 安装日志
        self.install_log = QTextEdit()
        self.install_log.setReadOnly(True)
        layout.addWidget(self.install_log)
        
        self.setLayout(layout)
        
        self.install_thread = None
    
    def initializePage(self):
        """开始安装"""
        self.install_log.clear()
        self.install_log.append("🚀 开始安装GPU支持组件...\n")
        
        # 获取选择的配置
        selection_page = self.wizard().page(1)
        selected_config = selection_page.config_group.checkedId()
        auto_install = selection_page.auto_install_checkbox.isChecked()
        
        if auto_install:
            self._start_installation(selected_config)
        else:
            self.install_log.append("⏭️ 跳过自动安装")
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(1)
    
    def _start_installation(self, config_type):
        """开始安装线程"""
        class InstallThread(QThread):
            log_signal = pyqtSignal(str)
            finished_signal = pyqtSignal(bool)
            
            def __init__(self, config_type):
                super().__init__()
                self.config_type = config_type
            
            def run(self):
                try:
                    # 根据配置类型安装相应组件
                    if self.config_type == 0:  # CUDA
                        self._install_cuda_support()
                    elif self.config_type == 1:  # DirectML
                        self._install_directml_support()
                    else:  # CPU
                        self._install_cpu_support()
                    
                    self.finished_signal.emit(True)
                except Exception as e:
                    self.log_signal.emit(f"❌ 安装失败: {e}")
                    self.finished_signal.emit(False)
            
            def _install_cuda_support(self):
                self.log_signal.emit("🚀 安装CUDA GPU支持...")
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'uninstall', 
                    'onnxruntime', 'onnxruntime-gpu', 'onnxruntime-directml', '-y'
                ], capture_output=True, text=True)
                
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', 'onnxruntime-gpu'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log_signal.emit("✅ CUDA GPU支持安装完成")
                else:
                    raise Exception(result.stderr)
            
            def _install_directml_support(self):
                self.log_signal.emit("⚡ 安装DirectML GPU支持...")
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'uninstall', 
                    'onnxruntime', 'onnxruntime-gpu', 'onnxruntime-directml', '-y'
                ], capture_output=True, text=True)
                
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', 'onnxruntime-directml'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log_signal.emit("✅ DirectML GPU支持安装完成")
                else:
                    raise Exception(result.stderr)
            
            def _install_cpu_support(self):
                self.log_signal.emit("💻 确保CPU支持...")
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', 'onnxruntime'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log_signal.emit("✅ CPU支持确认完成")
                else:
                    raise Exception(result.stderr)
        
        self.install_thread = InstallThread(config_type)
        self.install_thread.log_signal.connect(self.install_log.append)
        self.install_thread.finished_signal.connect(self._on_install_finished)
        self.install_thread.start()
    
    def _on_install_finished(self, success):
        """安装完成回调"""
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        
        if success:
            self.install_log.append("\n🎉 GPU支持安装完成！")
        else:
            self.install_log.append("\n❌ 安装过程中出现错误")


class GPUConfigWizard(QWizard):
    """GPU配置向导主窗口"""
    
    def __init__(self, gpu_config, parent=None):
        super().__init__(parent)
        self.gpu_config = gpu_config
        self.gpu_detection_result = {}
        
        self.setWindowTitle("🚀 GPU加速配置向导")
        self.setWizardStyle(QWizard.ModernStyle)
        self.setMinimumSize(600, 500)
        
        # 添加页面
        self.addPage(GPUDetectionPage(gpu_config))
        self.addPage(GPUConfigSelectionPage())
        self.addPage(GPUInstallationPage())
        
        # 设置按钮文本
        self.setButtonText(QWizard.NextButton, "下一步 >")
        self.setButtonText(QWizard.BackButton, "< 上一步")
        self.setButtonText(QWizard.FinishButton, "完成")
        self.setButtonText(QWizard.CancelButton, "取消")
