#!/usr/bin/env python3
"""
系统监测模块
提供实时的系统状态信息，包括CPU、内存、GPU使用情况
"""

import psutil
import platform
import time
import threading
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class SystemMonitor:
    """系统监测器"""

    def __init__(self):
        self.gpu_available = False
        self.nvidia_available = False
        self.amd_available = False
        self.intel_available = False

        # 监控线程控制
        self._monitoring = False
        self._monitor_thread = None
        self._lock = threading.Lock()

        # 缓存的监控数据
        self._cached_data = {
            'cpu': {},
            'memory': {},
            'gpu': {},
            'timestamp': 0
        }

        # GPU查询缓存（减少nvidia-smi调用频率）
        self._gpu_cache = {
            'data': None,
            'timestamp': 0,
            'cache_duration': 5.0  # 5秒缓存
        }

        self._check_gpu_availability()

    def _check_gpu_availability(self):
        """检查GPU是否可用"""
        try:
            import onnxruntime as ort
            providers = ort.get_available_providers()
            self.gpu_available = 'CUDAExecutionProvider' in providers or 'DmlExecutionProvider' in providers

            # 检查NVIDIA GPU
            if 'CUDAExecutionProvider' in providers:
                self.nvidia_available = True

            # 检查DirectML (AMD/Intel/NVIDIA)
            if 'DmlExecutionProvider' in providers:
                self.amd_available = True  # DirectML支持多种GPU

        except:
            self.gpu_available = False
    
    def get_all_info(self) -> Dict:
        """获取所有系统信息"""
        return {
            'cpu': self.get_cpu_info(),
            'memory': self.get_memory_info(),
            'gpu': self.get_gpu_info()
        }
    
    def get_cpu_info(self) -> Dict:
        """获取CPU信息"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            return {
                'usage_percent': cpu_percent,
                'core_count': cpu_count,
                'available': True
            }
        except Exception:
            return {
                'usage_percent': 0,
                'core_count': 0,
                'available': False
            }
    
    def get_memory_info(self) -> Dict:
        """获取内存信息"""
        try:
            memory = psutil.virtual_memory()
            
            return {
                'total_gb': round(memory.total / (1024**3), 1),
                'used_gb': round(memory.used / (1024**3), 1),
                'usage_percent': memory.percent,
                'available': True
            }
        except Exception:
            return {
                'total_gb': 0,
                'used_gb': 0,
                'usage_percent': 0,
                'available': False
            }
    
    def get_gpu_info(self) -> Dict:
        """获取GPU信息（带缓存优化）"""
        try:
            if not self.gpu_available:
                return {
                    'available': False,
                    'gpus': []
                }

            # 检查缓存是否有效
            current_time = time.time()
            if (self._gpu_cache['data'] is not None and
                current_time - self._gpu_cache['timestamp'] < self._gpu_cache['cache_duration']):
                return self._gpu_cache['data']

            gpu_info = {
                'available': True,
                'gpus': []
            }

            # 尝试获取NVIDIA GPU信息
            if self.nvidia_available:
                try:
                    import subprocess
                    result = subprocess.run([
                        'nvidia-smi', '--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu',
                        '--format=csv,noheader,nounits'
                    ], capture_output=True, text=True, timeout=3)  # 减少超时时间

                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        for i, line in enumerate(lines):
                            if line.strip():
                                parts = [p.strip() for p in line.split(',')]
                                if len(parts) >= 4:
                                    gpu_info['gpus'].append({
                                        'id': i,
                                        'name': parts[0],
                                        'utilization_percent': float(parts[1]) if parts[1] != '[Not Supported]' else 0,
                                        'memory_used_mb': float(parts[2]) if parts[2] != '[Not Supported]' else 0,
                                        'memory_total_mb': float(parts[3]) if parts[3] != '[Not Supported]' else 8192,
                                        'temperature': float(parts[4]) if len(parts) > 4 and parts[4] != '[Not Supported]' else 0,
                                        'type': 'NVIDIA'
                                    })
                except Exception as e:
                    logger.debug(f"nvidia-smi查询失败: {e}")
                    # 回退到基本信息
                    gpu_info['gpus'].append({
                        'id': 0,
                        'name': 'NVIDIA GPU',
                        'utilization_percent': 0,
                        'memory_used_mb': 0,
                        'memory_total_mb': 8192,
                        'temperature': 0,
                        'type': 'NVIDIA'
                    })

            # 如果没有获取到GPU信息，添加默认GPU
            if not gpu_info['gpus'] and self.gpu_available:
                gpu_info['gpus'].append({
                    'id': 0,
                    'name': 'GPU',
                    'utilization_percent': 0,
                    'memory_used_mb': 0,
                    'memory_total_mb': 4096,
                    'temperature': 0,
                    'type': 'Unknown'
                })

            # 更新缓存
            self._gpu_cache['data'] = gpu_info
            self._gpu_cache['timestamp'] = current_time

            return gpu_info

        except Exception as e:
            logger.error(f"获取GPU信息失败: {e}")
            return {
                'available': False,
                'gpus': []
            }
    
    def format_cpu_status(self, cpu_info: Dict) -> str:
        """格式化CPU状态"""
        if not cpu_info.get('available', False):
            return "CPU: 不可用"
        
        usage = cpu_info.get('usage_percent', 0)
        cores = cpu_info.get('core_count', 0)
        
        return f"CPU: {usage:.1f}% | {cores}核"
    
    def format_memory_status(self, memory_info: Dict) -> str:
        """格式化内存状态"""
        if not memory_info.get('available', False):
            return "内存: 不可用"
        
        used = memory_info.get('used_gb', 0)
        total = memory_info.get('total_gb', 0)
        usage = memory_info.get('usage_percent', 0)
        
        return f"内存: {usage:.1f}% | {used:.1f}G/{total:.1f}G"
    
    def format_gpu_status(self, gpu_info: Dict) -> str:
        """格式化GPU状态"""
        if not gpu_info.get('available', False):
            return "GPU: 不可用"
        
        gpus = gpu_info.get('gpus', [])
        if not gpus:
            return "GPU: 检测中"
        
        gpu = gpus[0]
        utilization = gpu.get('utilization_percent', 0)
        
        if utilization > 0:
            return f"GPU: {utilization:.1f}% | 运行中"
        else:
            return "GPU: 待机"
    
    def start_monitoring(self, interval: float = 2.0):
        """开始后台监控"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        logger.info("系统监控已启动")

    def stop_monitoring(self):
        """停止后台监控"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("系统监控已停止")

    def _monitor_loop(self, interval: float):
        """监控循环"""
        while self._monitoring:
            try:
                # 更新缓存数据
                with self._lock:
                    self._cached_data = {
                        'cpu': self.get_cpu_info(),
                        'memory': self.get_memory_info(),
                        'gpu': self.get_gpu_info(),
                        'timestamp': time.time()
                    }

                time.sleep(interval)
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                time.sleep(interval)

    def get_cached_info(self) -> Dict:
        """获取缓存的监控信息"""
        with self._lock:
            return self._cached_data.copy()

    def is_monitoring(self) -> bool:
        """检查是否正在监控"""
        return self._monitoring

    def update_gpu_usage(self, gpu_id: int, usage_percent: float):
        """更新GPU使用率（供外部调用）"""
        try:
            with self._lock:
                if 'gpu' in self._cached_data and self._cached_data['gpu'].get('available'):
                    gpus = self._cached_data['gpu'].get('gpus', [])
                    if 0 <= gpu_id < len(gpus):
                        gpus[gpu_id]['utilization_percent'] = usage_percent
        except Exception as e:
            logger.debug(f"更新GPU使用率失败: {e}")

    def get_system_summary(self) -> str:
        """获取系统状态摘要"""
        try:
            info = self.get_all_info()
            cpu_status = self.format_cpu_status(info['cpu'])
            memory_status = self.format_memory_status(info['memory'])
            gpu_status = self.format_gpu_status(info['gpu'])

            return f"{gpu_status} | {cpu_status} | {memory_status}"
        except Exception as e:
            logger.error(f"获取系统摘要失败: {e}")
            return "系统: 监控不可用"

    def __del__(self):
        """析构函数，确保监控线程正确停止"""
        try:
            self.stop_monitoring()
        except:
            pass
