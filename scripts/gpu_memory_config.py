#!/usr/bin/env python3
"""
GPU内存配置管理器
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

class GPUMemoryConfig:
    """GPU内存配置管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.config_file = self.config_dir / "gpu_memory.json"
        
        # 确保配置目录存在
        self.config_dir.mkdir(exist_ok=True)
        
        # 默认配置
        self.default_config = {
            "memory_limit_percent": 90,
            "memory_check_interval": 10,
            "auto_fallback_enabled": True,
            "max_gpu_errors": 5,
            "cleanup_interval": 50,
            "force_cpu_mode": False,
            "gpu_memory_limit_mb": 0,  # 0表示自动检测
            "enable_memory_monitoring": True
        }
        
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 合并默认配置（确保所有键都存在）
                for key, value in self.default_config.items():
                    if key not in config:
                        config[key] = value
                
                return config
            else:
                return self.default_config.copy()
        except Exception as e:
            print(f"加载GPU内存配置失败: {e}")
            return self.default_config.copy()
    
    def save_config(self) -> bool:
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存GPU内存配置失败: {e}")
            return False
    
    def get(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        self.config[key] = value
    
    def update(self, updates: Dict[str, Any]):
        """批量更新配置"""
        self.config.update(updates)
    
    def reset_to_default(self):
        """重置为默认配置"""
        self.config = self.default_config.copy()
    
    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config.copy()

def create_gpu_memory_config_gui():
    """创建GPU内存配置GUI"""
    try:
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                                   QLabel, QSpinBox, QCheckBox, QPushButton,
                                   QGroupBox, QFormLayout, QMessageBox)
        from PyQt5.QtCore import Qt
        
        class GPUMemoryConfigDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.config_manager = GPUMemoryConfig()
                self.init_ui()
                self.load_current_config()
            
            def init_ui(self):
                self.setWindowTitle("GPU内存使用配置")
                self.setFixedSize(400, 500)
                
                layout = QVBoxLayout(self)
                
                # 内存限制组
                memory_group = QGroupBox("内存限制设置")
                memory_layout = QFormLayout(memory_group)
                
                self.memory_limit_spin = QSpinBox()
                self.memory_limit_spin.setRange(50, 95)
                self.memory_limit_spin.setSuffix("%")
                memory_layout.addRow("GPU内存使用限制:", self.memory_limit_spin)
                
                self.memory_check_interval_spin = QSpinBox()
                self.memory_check_interval_spin.setRange(1, 100)
                self.memory_check_interval_spin.setSuffix(" 帧")
                memory_layout.addRow("内存检查间隔:", self.memory_check_interval_spin)
                
                layout.addWidget(memory_group)
                
                # 错误处理组
                error_group = QGroupBox("错误处理设置")
                error_layout = QFormLayout(error_group)
                
                self.auto_fallback_check = QCheckBox("启用自动回退到CPU")
                error_layout.addRow(self.auto_fallback_check)
                
                self.max_errors_spin = QSpinBox()
                self.max_errors_spin.setRange(1, 20)
                self.max_errors_spin.setSuffix(" 次")
                error_layout.addRow("最大GPU错误次数:", self.max_errors_spin)
                
                layout.addWidget(error_group)
                
                # 性能优化组
                perf_group = QGroupBox("性能优化设置")
                perf_layout = QFormLayout(perf_group)
                
                self.cleanup_interval_spin = QSpinBox()
                self.cleanup_interval_spin.setRange(10, 200)
                self.cleanup_interval_spin.setSuffix(" 帧")
                perf_layout.addRow("内存清理间隔:", self.cleanup_interval_spin)
                
                self.enable_monitoring_check = QCheckBox("启用内存监控")
                perf_layout.addRow(self.enable_monitoring_check)
                
                layout.addWidget(perf_group)
                
                # 高级设置组
                advanced_group = QGroupBox("高级设置")
                advanced_layout = QFormLayout(advanced_group)
                
                self.force_cpu_check = QCheckBox("强制使用CPU模式")
                advanced_layout.addRow(self.force_cpu_check)
                
                self.gpu_memory_limit_spin = QSpinBox()
                self.gpu_memory_limit_spin.setRange(0, 16384)
                self.gpu_memory_limit_spin.setSuffix(" MB (0=自动)")
                advanced_layout.addRow("GPU内存限制:", self.gpu_memory_limit_spin)
                
                layout.addWidget(advanced_group)
                
                # 按钮组
                button_layout = QHBoxLayout()
                
                self.reset_button = QPushButton("重置默认")
                self.reset_button.clicked.connect(self.reset_to_default)
                button_layout.addWidget(self.reset_button)
                
                self.cancel_button = QPushButton("取消")
                self.cancel_button.clicked.connect(self.reject)
                button_layout.addWidget(self.cancel_button)
                
                self.save_button = QPushButton("保存")
                self.save_button.clicked.connect(self.save_config)
                button_layout.addWidget(self.save_button)
                
                layout.addLayout(button_layout)
            
            def load_current_config(self):
                """加载当前配置到界面"""
                config = self.config_manager.get_all_config()
                
                self.memory_limit_spin.setValue(config['memory_limit_percent'])
                self.memory_check_interval_spin.setValue(config['memory_check_interval'])
                self.auto_fallback_check.setChecked(config['auto_fallback_enabled'])
                self.max_errors_spin.setValue(config['max_gpu_errors'])
                self.cleanup_interval_spin.setValue(config['cleanup_interval'])
                self.enable_monitoring_check.setChecked(config['enable_memory_monitoring'])
                self.force_cpu_check.setChecked(config['force_cpu_mode'])
                self.gpu_memory_limit_spin.setValue(config['gpu_memory_limit_mb'])
            
            def save_config(self):
                """保存配置"""
                try:
                    updates = {
                        'memory_limit_percent': self.memory_limit_spin.value(),
                        'memory_check_interval': self.memory_check_interval_spin.value(),
                        'auto_fallback_enabled': self.auto_fallback_check.isChecked(),
                        'max_gpu_errors': self.max_errors_spin.value(),
                        'cleanup_interval': self.cleanup_interval_spin.value(),
                        'enable_memory_monitoring': self.enable_monitoring_check.isChecked(),
                        'force_cpu_mode': self.force_cpu_check.isChecked(),
                        'gpu_memory_limit_mb': self.gpu_memory_limit_spin.value()
                    }
                    
                    self.config_manager.update(updates)
                    
                    if self.config_manager.save_config():
                        QMessageBox.information(self, "保存成功", "GPU内存配置已保存")
                        self.accept()
                    else:
                        QMessageBox.critical(self, "保存失败", "无法保存配置文件")
                        
                except Exception as e:
                    QMessageBox.critical(self, "配置失败", f"保存配置时出错: {e}")
            
            def reset_to_default(self):
                """重置为默认配置"""
                self.config_manager.reset_to_default()
                self.load_current_config()
                QMessageBox.information(self, "重置完成", "已重置为默认配置")
        
        return GPUMemoryConfigDialog
        
    except ImportError:
        print("PyQt5未安装，无法创建GUI")
        return None

# 兼容性函数，供主程序调用
_global_config_manager = None

def get_config_manager():
    """获取全局配置管理器实例"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = GPUMemoryConfig()
    return _global_config_manager

def load_config():
    """加载配置（兼容性函数）"""
    return get_config_manager().get_all_config()

def save_config(config_dict):
    """保存配置（兼容性函数）"""
    try:
        manager = get_config_manager()
        manager.update(config_dict)
        return manager.save_config()
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False

def main():
    """主函数"""
    import sys

    # 测试配置管理器
    config_manager = GPUMemoryConfig()
    print("当前GPU内存配置:")
    for key, value in config_manager.get_all_config().items():
        print(f"  {key}: {value}")

    # 如果有PyQt5，启动GUI
    try:
        from PyQt5.QtWidgets import QApplication

        app = QApplication(sys.argv)

        dialog_class = create_gpu_memory_config_gui()
        if dialog_class:
            dialog = dialog_class()
            dialog.exec_()

    except ImportError:
        print("PyQt5未安装，仅显示当前配置")

if __name__ == "__main__":
    main()
