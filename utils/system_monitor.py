#!/usr/bin/env python3
"""
系统资源监控工具
监控GPU、CPU、内存使用情况
"""

import psutil
import subprocess
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SystemMonitor:
    """系统资源监控器"""
    
    def __init__(self):
        self.nvidia_available = self._check_nvidia_smi()
    
    def _check_nvidia_smi(self) -> bool:
        """检查nvidia-smi是否可用"""
        try:
            subprocess.run(['nvidia-smi'], capture_output=True, check=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False
    
    def get_gpu_info(self) -> Dict:
        """获取GPU信息"""
        if not self.nvidia_available:
            return {
                'available': False,
                'error': 'nvidia-smi not available'
            }
        
        try:
            # 使用nvidia-smi获取GPU信息
            cmd = [
                'nvidia-smi',
                '--query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu',
                '--format=csv,noheader,nounits'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpus = []
                
                for line in lines:
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 6:
                            try:
                                gpu_info = {
                                    'index': int(parts[0]),
                                    'name': parts[1],
                                    'memory_used_mb': int(parts[2]),
                                    'memory_total_mb': int(parts[3]),
                                    'utilization_percent': int(parts[4]),
                                    'temperature_c': int(parts[5]) if parts[5] != 'N/A' else None
                                }
                                gpus.append(gpu_info)
                            except ValueError:
                                continue
                
                return {
                    'available': True,
                    'count': len(gpus),
                    'gpus': gpus
                }
            else:
                return {
                    'available': False,
                    'error': f'nvidia-smi failed: {result.stderr}'
                }
                
        except subprocess.TimeoutExpired:
            return {
                'available': False,
                'error': 'nvidia-smi timeout'
            }
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def get_cpu_info(self) -> Dict:
        """获取CPU信息"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            return {
                'available': True,
                'usage_percent': cpu_percent,
                'core_count': cpu_count,
                'frequency_mhz': cpu_freq.current if cpu_freq else None
            }
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def get_memory_info(self) -> Dict:
        """获取内存信息"""
        try:
            memory = psutil.virtual_memory()
            
            return {
                'available': True,
                'total_gb': memory.total / (1024**3),
                'used_gb': memory.used / (1024**3),
                'available_gb': memory.available / (1024**3),
                'usage_percent': memory.percent
            }
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def get_all_info(self) -> Dict:
        """获取所有系统信息"""
        return {
            'gpu': self.get_gpu_info(),
            'cpu': self.get_cpu_info(),
            'memory': self.get_memory_info()
        }
    
    def format_gpu_status(self, gpu_info: Dict) -> str:
        """格式化GPU状态显示"""
        if not gpu_info.get('available'):
            return "GPU: 不可用"
        
        gpus = gpu_info.get('gpus', [])
        if not gpus:
            return "GPU: 无设备"
        
        # 显示第一个GPU的信息
        gpu = gpus[0]
        used_mb = gpu['memory_used_mb']
        total_mb = gpu['memory_total_mb']
        usage_percent = gpu['utilization_percent']
        
        used_gb = used_mb / 1024
        total_gb = total_mb / 1024
        
        return f"GPU: {usage_percent}% | {used_gb:.1f}G/{total_gb:.1f}G"
    
    def format_cpu_status(self, cpu_info: Dict) -> str:
        """格式化CPU状态显示"""
        if not cpu_info.get('available'):
            return "CPU: 不可用"
        
        usage = cpu_info['usage_percent']
        cores = cpu_info['core_count']
        
        return f"CPU: {usage:.1f}% | {cores}核"
    
    def format_memory_status(self, memory_info: Dict) -> str:
        """格式化内存状态显示"""
        if not memory_info.get('available'):
            return "内存: 不可用"
        
        used_gb = memory_info['used_gb']
        total_gb = memory_info['total_gb']
        usage_percent = memory_info['usage_percent']
        
        return f"内存: {usage_percent:.1f}% | {used_gb:.1f}G/{total_gb:.1f}G"

def main():
    """测试函数"""
    monitor = SystemMonitor()
    info = monitor.get_all_info()
    
    print("系统资源监控:")
    print("=" * 50)
    
    # GPU信息
    gpu_info = info['gpu']
    print(f"GPU状态: {monitor.format_gpu_status(gpu_info)}")
    
    # CPU信息
    cpu_info = info['cpu']
    print(f"CPU状态: {monitor.format_cpu_status(cpu_info)}")
    
    # 内存信息
    memory_info = info['memory']
    print(f"内存状态: {monitor.format_memory_status(memory_info)}")

if __name__ == "__main__":
    main()
