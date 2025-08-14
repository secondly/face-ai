"""
下载管理器GUI - 用于下载模型和工具
使用InsightFace官方方式确保下载成功
"""

import sys
import threading
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import logging

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))
from auto_downloader import AutoDownloader

logger = logging.getLogger(__name__)


class DownloadWorker(QThread):
    """下载工作线程"""

    progress_updated = pyqtSignal(str, object)  # 消息, 进度百分比(可以是None)
    download_finished = pyqtSignal(bool)  # 是否成功
    
    def __init__(self, downloader: AutoDownloader):
        super().__init__()
        self.downloader = downloader
        self.is_cancelled = False
    
    def run(self):
        """执行下载"""
        try:
            def progress_callback(message, progress):
                if not self.is_cancelled:
                    self.progress_updated.emit(message, progress)
            
            success = self.downloader.download_all(progress_callback)
            self.download_finished.emit(success)
            
        except Exception as e:
            logger.error(f"下载线程出错: {e}")
            self.download_finished.emit(False)
    
    def cancel(self):
        """取消下载"""
        self.is_cancelled = True


class DownloadManagerDialog(QDialog):
    """下载管理器对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.downloader = AutoDownloader()
        self.worker = None
        
        self.setWindowTitle("AI换脸工具 - 首次配置")
        self.setFixedSize(650, 700)  # 增加宽度和高度，适应更大的状态显示区域
        self.setModal(True)
        
        self._setup_ui()
        self._check_requirements()
    
    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title_label = QLabel("🎭 欢迎使用AI换脸工具")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #333; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 说明文本
        info_label = QLabel(
            "首次使用需要下载必要的模型文件和工具。\n"
            "使用InsightFace官方下载方式，确保成功率。\n"
            "总大小约800MB，请确保网络连接稳定。"
        )
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 14px; margin-bottom: 20px;")
        layout.addWidget(info_label)
        
        # 文件状态区域
        status_group = QGroupBox("文件状态检查")
        status_layout = QVBoxLayout(status_group)
        
        self.status_text = QTextEdit()
        self.status_text.setMinimumHeight(320)  # 增加到320像素，是原来的2倍多
        self.status_text.setMaximumHeight(400)  # 设置最大高度避免过大
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f8f9fa;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                padding: 15px;
                line-height: 1.4;
            }
        """)
        status_layout.addWidget(self.status_text)
        layout.addWidget(status_group)
        
        # 进度区域
        progress_group = QGroupBox("下载进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_label = QLabel("准备就绪")
        self.progress_label.setStyleSheet("color: #333; font-size: 12px;")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
                font-weight: bold;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        layout.addWidget(progress_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.download_button = QPushButton("🚀 开始下载")
        self.download_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.download_button.clicked.connect(self._start_download)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        self.cancel_button.clicked.connect(self._cancel_download)
        
        self.skip_button = QPushButton("跳过下载")
        self.skip_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        self.skip_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.skip_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.download_button)
        
        layout.addLayout(button_layout)
    
    def _check_requirements(self):
        """检查必需文件"""
        self.status_text.clear()
        self.status_text.append("🔍 检查必需文件...")
        
        status = self.downloader.check_requirements()
        
        # 检查模型文件
        self.status_text.append("\n📁 模型文件:")
        all_models_exist = True
        for model_name, exists in status['models'].items():
            icon = "✅" if exists else "❌"
            self.status_text.append(f"  {icon} {model_name}")
            if not exists:
                all_models_exist = False
        
        # 检查FFmpeg
        self.status_text.append("\n🛠️ FFmpeg工具:")
        all_ffmpeg_exist = True
        for tool_name, exists in status['ffmpeg'].items():
            icon = "✅" if exists else "❌"
            self.status_text.append(f"  {icon} {tool_name}")
            if not exists:
                all_ffmpeg_exist = False
        
        # 总结
        if all_models_exist and all_ffmpeg_exist:
            self.status_text.append("\n🎉 所有文件已就绪！可以直接使用。")
            self.download_button.setText("✅ 文件完整")
            self.download_button.setEnabled(False)
            self.skip_button.setText("继续使用")
        else:
            missing_count = sum(1 for exists in status['models'].values() if not exists)
            missing_count += sum(1 for exists in status['ffmpeg'].values() if not exists)
            self.status_text.append(f"\n⚠️ 缺少 {missing_count} 个文件，需要下载。")
            self.status_text.append("\n📋 下载步骤:")
            self.status_text.append("  1. 安装InsightFace依赖")
            self.status_text.append("  2. 下载buffalo_l模型包")
            self.status_text.append("  3. 下载inswapper模型")
            self.status_text.append("  4. 复制模型到项目")
            self.status_text.append("  5. 下载FFmpeg工具")
    
    def _start_download(self):
        """开始下载"""
        if self.worker and self.worker.isRunning():
            return
        
        self.download_button.setEnabled(False)
        self.skip_button.setEnabled(False)
        self.cancel_button.setText("取消下载")
        
        # 创建并启动下载线程
        self.worker = DownloadWorker(self.downloader)
        self.worker.progress_updated.connect(self._update_progress)
        self.worker.download_finished.connect(self._download_finished)
        self.worker.start()
    
    def _update_progress(self, message: str, progress):
        """更新进度"""
        self.progress_label.setText(message)
        if progress is not None and isinstance(progress, (int, float)):
            # 确保进度值在0-100范围内
            progress_value = max(0, min(100, int(progress)))
            self.progress_bar.setValue(progress_value)
        # 如果progress为None或无效，保持当前进度条值不变
    
    def _download_finished(self, success: bool):
        """下载完成"""
        if success:
            self.progress_label.setText("✅ 下载完成！")
            self.progress_bar.setValue(100)
            QMessageBox.information(self, "下载完成", "所有文件下载完成！现在可以使用AI换脸工具了。")
            self.accept()
        else:
            self.progress_label.setText("❌ 下载失败")
            QMessageBox.warning(self, "下载失败", 
                              "文件下载失败，请检查网络连接后重试。\n\n"
                              "建议:\n"
                              "1. 检查网络连接\n"
                              "2. 确保有足够的磁盘空间\n"
                              "3. 尝试使用VPN或更换网络环境")
            self._reset_buttons()
    
    def _cancel_download(self):
        """取消下载"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
            self.progress_label.setText("下载已取消")
            self.progress_bar.setValue(0)
            self._reset_buttons()
        else:
            self.reject()
    
    def _reset_buttons(self):
        """重置按钮状态"""
        self.download_button.setEnabled(True)
        self.skip_button.setEnabled(True)
        self.cancel_button.setText("取消")


def show_download_manager(parent=None) -> bool:
    """显示下载管理器，返回是否成功"""
    dialog = DownloadManagerDialog(parent)
    result = dialog.exec_()
    return result == QDialog.Accepted


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("AI换脸工具下载器")
    app.setApplicationVersion("1.0")
    
    success = show_download_manager()
    print(f"下载结果: {'成功' if success else '取消/失败'}")
