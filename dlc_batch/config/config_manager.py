"""
配置管理器

负责配置文件加载、参数验证、环境变量处理等。
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from ..utils.logger import LoggerMixin
from .default_config import (
    get_default_config, 
    get_quality_preset, 
    apply_env_vars,
    QUALITY_PRESETS
)

class ConfigManager(LoggerMixin):
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，None使用默认配置
        """
        self.config_file = Path(config_file) if config_file else None
        self.config = get_default_config()
        
        # 加载配置文件
        if self.config_file and self.config_file.exists():
            self.load_config_file()
        
        # 应用环境变量
        self.config = apply_env_vars(self.config)
        
        self.logger.info("配置管理器初始化完成")
    
    def load_config_file(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
            
            if file_config:
                self.config = self._merge_configs(self.config, file_config)
                self.logger.info(f"配置文件加载成功: {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"配置文件加载失败: {e}")
            raise
    
    def save_config_file(self, file_path: Optional[str] = None):
        """保存配置到文件"""
        save_path = Path(file_path) if file_path else self.config_file
        
        if not save_path:
            raise ValueError("未指定保存路径")
        
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            
            self.logger.info(f"配置文件保存成功: {save_path}")
            
        except Exception as e:
            self.logger.error(f"配置文件保存失败: {e}")
            raise
    
    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """递归合并配置字典"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值 (支持点分隔的嵌套键)
        
        Args:
            key: 配置键，支持 'section.subsection.key' 格式
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        keys = key.split('.')
        current = self.config
        
        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        设置配置值 (支持点分隔的嵌套键)
        
        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        current = self.config
        
        # 导航到目标位置
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # 设置值
        current[keys[-1]] = value
        self.logger.debug(f"配置更新: {key} = {value}")
    
    def apply_quality_preset(self, quality: str):
        """
        应用质量预设
        
        Args:
            quality: 质量级别 ('fast', 'balanced', 'high')
        """
        if quality not in QUALITY_PRESETS:
            raise ValueError(f"未知的质量预设: {quality}")
        
        preset = get_quality_preset(quality)
        self.config = self._merge_configs(self.config, preset)
        self.logger.info(f"应用质量预设: {quality}")
    
    def validate_config(self) -> Dict[str, list]:
        """
        验证配置有效性
        
        Returns:
            Dict[str, list]: 验证结果 {'errors': [...], 'warnings': [...]}
        """
        errors = []
        warnings = []
        
        # 验证模型文件路径
        model_paths = self.get('models', {})
        for model_name, model_path in model_paths.items():
            if not Path(model_path).exists():
                errors.append(f"模型文件不存在: {model_name} -> {model_path}")
        
        # 验证路径配置
        paths = self.get('paths', {})
        for path_name, path_value in paths.items():
            if path_name.endswith('_dir'):
                path_obj = Path(path_value)
                if not path_obj.exists():
                    warnings.append(f"目录不存在: {path_name} -> {path_value}")
        
        # 验证数值范围
        conf_threshold = self.get('detection.conf_threshold', 0.5)
        if not 0 <= conf_threshold <= 1:
            errors.append(f"检测置信度阈值超出范围 [0,1]: {conf_threshold}")
        
        blend_ratio = self.get('swapping.blend_ratio', 0.8)
        if not 0 <= blend_ratio <= 1:
            errors.append(f"融合比例超出范围 [0,1]: {blend_ratio}")
        
        # 验证提供者
        providers = self.get('performance.providers', [])
        if not providers:
            warnings.append("未配置推理提供者")
        
        return {'errors': errors, 'warnings': warnings}
    
    def get_model_path(self, model_name: str) -> str:
        """
        获取模型文件路径
        
        Args:
            model_name: 模型名称
            
        Returns:
            str: 模型文件路径
        """
        return self.get(f'models.{model_name}', '')
    
    def get_providers(self) -> list:
        """获取推理提供者列表"""
        return self.get('performance.providers', ['CPUExecutionProvider'])
    
    def get_detection_config(self) -> Dict[str, Any]:
        """获取检测配置"""
        return self.get('detection', {})
    
    def get_swapping_config(self) -> Dict[str, Any]:
        """获取换脸配置"""
        return self.get('swapping', {})
    
    def get_output_config(self) -> Dict[str, Any]:
        """获取输出配置"""
        return self.get('output', {})
    
    def update_from_args(self, args: Dict[str, Any]):
        """
        从命令行参数更新配置
        
        Args:
            args: 命令行参数字典
        """
        # 映射命令行参数到配置键
        arg_mapping = {
            'quality': lambda v: self.apply_quality_preset(v),
            'providers': 'performance.providers',
            'conf_threshold': 'detection.conf_threshold',
            'enhance_face': 'swapping.enhance_face',
            'color_correction': 'swapping.color_correction',
            'use_segmentation': 'swapping.use_segmentation',
            'fps': 'output.fps',
            'codec': 'output.codec',
        }
        
        for arg_name, config_key in arg_mapping.items():
            if arg_name in args and args[arg_name] is not None:
                if callable(config_key):
                    config_key(args[arg_name])
                else:
                    self.set(config_key, args[arg_name])
    
    def to_dict(self) -> Dict[str, Any]:
        """返回配置字典的副本"""
        return self.config.copy()
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"ConfigManager(config_file={self.config_file})"

def create_default_config_file(file_path: str):
    """
    创建默认配置文件
    
    Args:
        file_path: 配置文件路径
    """
    config_manager = ConfigManager()
    config_manager.save_config_file(file_path)

def load_config(config_file: Optional[str] = None, 
               quality: Optional[str] = None,
               **overrides) -> ConfigManager:
    """
    便捷的配置加载函数
    
    Args:
        config_file: 配置文件路径
        quality: 质量预设
        **overrides: 配置覆盖
        
    Returns:
        ConfigManager: 配置管理器实例
    """
    config_manager = ConfigManager(config_file)
    
    if quality:
        config_manager.apply_quality_preset(quality)
    
    for key, value in overrides.items():
        config_manager.set(key, value)
    
    return config_manager
