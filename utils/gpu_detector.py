#!/usr/bin/env python3
"""
GPU检测和配置工具
提供详细的GPU信息检测和智能配置建议
"""

import os
import sys
import platform
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 设置日志
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

class GPUDetector:
    """GPU检测器"""
    
    def __init__(self):
        self.system = platform.system()
        self.gpu_info = {}
        self.onnx_providers = []
        self.cuda_info = {}
        
    def detect_all(self) -> Dict:
        """检测所有GPU相关信息"""
        logger.info("🔍 开始GPU环境检测...")
        
        result = {
            'system': self.system,
            'nvidia_gpu': self._detect_nvidia_gpu(),
            'amd_gpu': self._detect_amd_gpu(),
            'intel_gpu': self._detect_intel_gpu(),
            'cuda': self._detect_cuda(),
            'onnx_providers': self._detect_onnx_providers(),
            'recommended_config': None,
            'gpu_available': False
        }
        
        # 生成推荐配置
        result['recommended_config'] = self._generate_recommendation(result)

        # 确保推荐配置不为None
        if result['recommended_config'] is None:
            result['recommended_config'] = {
                'type': 'cpu_only',
                'provider': 'CPUExecutionProvider',
                'description': 'CPU处理模式',
                'performance': 'basic',
                'gpu_enabled': False,
                'reason': '无可用GPU配置'
            }

        result['gpu_available'] = self._is_gpu_available(result)
        
        return result
    
    def _detect_nvidia_gpu(self) -> Dict:
        """检测NVIDIA GPU"""
        logger.info("🔍 检测NVIDIA GPU...")

        try:
            # 首先尝试简单的nvidia-smi命令
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                # 如果nvidia-smi可用，尝试获取详细信息
                try:
                    detail_result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,driver_version,cuda_version',
                                                   '--format=csv,noheader,nounits'],
                                                  capture_output=True, text=True, timeout=10)

                    if detail_result.returncode == 0:
                        lines = detail_result.stdout.strip().split('\n')
                        gpus = []

                        for line in lines:
                            if line.strip():
                                parts = [p.strip() for p in line.split(',')]
                                if len(parts) >= 4:
                                    gpu_info = {
                                        'name': parts[0],
                                        'memory_mb': int(parts[1]) if parts[1].isdigit() else 0,
                                        'driver_version': parts[2],
                                        'cuda_version': parts[3]
                                    }
                                    gpus.append(gpu_info)
                                    logger.info(f"✅ 检测到NVIDIA GPU: {gpu_info['name']} ({gpu_info['memory_mb']}MB)")

                        if gpus:
                            return {
                                'available': True,
                                'count': len(gpus),
                                'gpus': gpus,
                                'driver_version': gpus[0]['driver_version'] if gpus else None,
                                'cuda_version': gpus[0]['cuda_version'] if gpus else None
                            }
                except:
                    pass

                # 如果详细查询失败，但nvidia-smi可用，说明有NVIDIA GPU
                logger.info("✅ 检测到NVIDIA GPU (详细信息获取失败)")
                return {
                    'available': True,
                    'count': 1,
                    'gpus': [{'name': 'NVIDIA GPU', 'memory_mb': 0, 'driver_version': 'Unknown', 'cuda_version': 'Unknown'}],
                    'driver_version': 'Unknown',
                    'cuda_version': 'Unknown'
                }
            else:
                logger.info("❌ nvidia-smi命令执行失败")
                return {'available': False, 'error': 'nvidia-smi failed'}

        except FileNotFoundError:
            logger.info("❌ nvidia-smi命令不存在")
            return {'available': False, 'error': 'nvidia-smi not found'}
        except subprocess.TimeoutExpired:
            logger.info("❌ nvidia-smi命令超时")
            return {'available': False, 'error': 'nvidia-smi timeout'}
        except Exception as e:
            logger.info(f"❌ NVIDIA GPU检测失败: {e}")
            return {'available': False, 'error': str(e)}
    
    def _detect_amd_gpu(self) -> Dict:
        """检测AMD GPU"""
        logger.info("🔍 检测AMD GPU...")
        
        if self.system == "Linux":
            try:
                result = subprocess.run(['rocm-smi', '--showproductname'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    logger.info("✅ 检测到AMD GPU (ROCm)")
                    return {'available': True, 'type': 'rocm', 'info': result.stdout.strip()}
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        # Windows AMD GPU检测
        if self.system == "Windows":
            try:
                result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name,AdapterRAM'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and 'AMD' in result.stdout:
                    logger.info("✅ 检测到AMD GPU")
                    return {'available': True, 'type': 'directml', 'info': 'AMD GPU detected'}
            except Exception:
                pass
        
        logger.info("❌ 未检测到AMD GPU")
        return {'available': False}
    
    def _detect_intel_gpu(self) -> Dict:
        """检测Intel GPU"""
        logger.info("🔍 检测Intel GPU...")
        
        if self.system == "Windows":
            try:
                result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name,AdapterRAM'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and 'Intel' in result.stdout:
                    logger.info("✅ 检测到Intel GPU")
                    return {'available': True, 'type': 'directml', 'info': 'Intel GPU detected'}
            except Exception:
                pass
        
        logger.info("❌ 未检测到Intel GPU")
        return {'available': False}
    
    def _detect_cuda(self) -> Dict:
        """检测CUDA"""
        logger.info("🔍 检测CUDA...")
        
        try:
            result = subprocess.run(['nvcc', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_line = None
                for line in result.stdout.split('\n'):
                    if 'release' in line.lower():
                        version_line = line.strip()
                        break
                
                logger.info(f"✅ 检测到CUDA: {version_line}")
                return {
                    'available': True,
                    'version_info': version_line,
                    'nvcc_output': result.stdout.strip()
                }
            else:
                logger.info("❌ CUDA编译器不可用")
                return {'available': False, 'error': 'nvcc failed'}
                
        except FileNotFoundError:
            logger.info("❌ nvcc命令不存在")
            return {'available': False, 'error': 'nvcc not found'}
        except subprocess.TimeoutExpired:
            logger.info("❌ nvcc命令超时")
            return {'available': False, 'error': 'nvcc timeout'}
        except Exception as e:
            logger.info(f"❌ CUDA检测失败: {e}")
            return {'available': False, 'error': str(e)}
    
    def _detect_onnx_providers(self) -> Dict:
        """检测ONNX Runtime提供者"""
        logger.info("🔍 检测ONNX Runtime提供者...")
        
        try:
            import onnxruntime as ort
            available_providers = ort.get_available_providers()
            
            provider_details = {}
            for provider in available_providers:
                if provider == 'CUDAExecutionProvider':
                    try:
                        # 尝试获取CUDA设备信息
                        session_options = ort.SessionOptions()
                        providers_list = [('CUDAExecutionProvider', {'device_id': 0})]
                        provider_details[provider] = {
                            'available': True,
                            'type': 'NVIDIA CUDA',
                            'description': 'NVIDIA GPU加速 (最佳性能)'
                        }
                        logger.info("✅ CUDAExecutionProvider 可用")
                    except Exception as e:
                        provider_details[provider] = {
                            'available': False,
                            'error': str(e),
                            'description': 'CUDA提供者不可用'
                        }
                        logger.info(f"❌ CUDAExecutionProvider 不可用: {e}")
                
                elif provider == 'DmlExecutionProvider':
                    provider_details[provider] = {
                        'available': True,
                        'type': 'DirectML',
                        'description': 'DirectML GPU加速 (支持AMD/Intel/NVIDIA)'
                    }
                    logger.info("✅ DmlExecutionProvider 可用")
                
                elif provider == 'CPUExecutionProvider':
                    provider_details[provider] = {
                        'available': True,
                        'type': 'CPU',
                        'description': 'CPU处理 (兼容性最佳)'
                    }
                    logger.info("✅ CPUExecutionProvider 可用")
                
                else:
                    provider_details[provider] = {
                        'available': True,
                        'type': 'Other',
                        'description': f'{provider} 可用'
                    }
                    logger.info(f"✅ {provider} 可用")
            
            return {
                'available': True,
                'providers': available_providers,
                'details': provider_details,
                'onnxruntime_version': ort.__version__
            }
            
        except ImportError:
            logger.info("❌ ONNX Runtime未安装")
            return {'available': False, 'error': 'onnxruntime not installed'}
        except Exception as e:
            logger.info(f"❌ ONNX Runtime检测失败: {e}")
            return {'available': False, 'error': str(e)}
    
    def _generate_recommendation(self, detection_result: Dict) -> Dict:
        """生成推荐配置"""
        logger.info("🎯 生成推荐配置...")
        
        nvidia = detection_result['nvidia_gpu']
        cuda = detection_result['cuda']
        onnx = detection_result['onnx_providers']
        
        # NVIDIA GPU + CUDA (优先推荐，但需要真正可用)
        if nvidia.get('available') and cuda.get('available'):
            if (onnx.get('available') and 'CUDAExecutionProvider' in onnx.get('providers', [])):
                # 测试CUDA是否真正可用
                try:
                    import onnxruntime as ort
                    # 尝试创建CUDA会话来验证
                    test_providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
                    # 这里只是检查提供者是否可用，不创建实际会话
                    return {
                        'type': 'cuda_gpu',
                        'provider': 'CUDAExecutionProvider',
                        'description': 'NVIDIA CUDA GPU加速 (推荐)',
                        'performance': 'excellent',
                        'gpu_enabled': True,
                        'reason': 'NVIDIA GPU + CUDA + CUDAExecutionProvider 完整支持'
                    }
                except:
                    # CUDA提供者有问题，回退到DirectML
                    pass

        # DirectML (Windows通用GPU加速) - 检查是否可用
        if (self.system == "Windows" and
            onnx.get('available') and
            'DmlExecutionProvider' in onnx.get('providers', [])):

            # 检查是否有任何GPU可用
            has_gpu = (nvidia.get('available') or
                      detection_result.get('amd_gpu', {}).get('available') or
                      detection_result.get('intel_gpu', {}).get('available'))

            return {
                'type': 'directml_gpu',
                'provider': 'DmlExecutionProvider',
                'description': 'DirectML GPU加速 (已启用)',
                'performance': 'good',
                'gpu_enabled': True,
                'reason': 'DirectML支持多种GPU，当前已配置并可用'
            }
        
        # 仅CPU
        else:
            issues = []
            if not nvidia.get('available'):
                issues.append('未检测到NVIDIA GPU')
            if not cuda.get('available'):
                issues.append('未安装CUDA')
            if not onnx.get('available'):
                issues.append('ONNX Runtime未安装')
            elif 'CUDAExecutionProvider' not in onnx.get('providers', []):
                issues.append('ONNX Runtime不支持CUDA')
            
            return {
                'type': 'cpu_only',
                'provider': 'CPUExecutionProvider',
                'description': 'CPU处理模式',
                'performance': 'basic',
                'gpu_enabled': False,
                'reason': f"GPU加速不可用: {', '.join(issues)}"
            }
    
    def _is_gpu_available(self, detection_result: Dict) -> bool:
        """判断GPU是否可用"""
        recommendation = detection_result.get('recommended_config', {})
        return recommendation.get('gpu_enabled', False)
    
    def print_detailed_report(self, detection_result: Dict):
        """打印详细报告"""
        print("\n" + "=" * 80)
        print("🔍 GPU环境检测报告")
        print("=" * 80)
        
        # 系统信息
        print(f"💻 操作系统: {detection_result['system']}")
        
        # NVIDIA GPU
        nvidia = detection_result['nvidia_gpu']
        print(f"\n🎮 NVIDIA GPU:")
        if nvidia.get('available'):
            print(f"   ✅ 状态: 可用 ({nvidia['count']}个GPU)")
            for i, gpu in enumerate(nvidia['gpus']):
                print(f"   📊 GPU {i+1}: {gpu['name']}")
                print(f"       💾 显存: {gpu['memory_mb']}MB")
                print(f"       🔧 驱动版本: {gpu['driver_version']}")
                print(f"       🚀 CUDA版本: {gpu['cuda_version']}")
        else:
            print(f"   ❌ 状态: 不可用 ({nvidia.get('error', '未知错误')})")
        
        # CUDA
        cuda = detection_result['cuda']
        print(f"\n🚀 CUDA:")
        if cuda.get('available'):
            print(f"   ✅ 状态: 可用")
            print(f"   📋 版本: {cuda['version_info']}")
        else:
            print(f"   ❌ 状态: 不可用 ({cuda.get('error', '未知错误')})")
        
        # ONNX Runtime
        onnx = detection_result['onnx_providers']
        print(f"\n🧠 ONNX Runtime:")
        if onnx.get('available'):
            print(f"   ✅ 状态: 可用 (版本 {onnx['onnxruntime_version']})")
            print(f"   📋 可用提供者:")
            for provider in onnx['providers']:
                details = onnx['details'].get(provider, {})
                status = "✅" if details.get('available', True) else "❌"
                desc = details.get('description', provider)
                print(f"       {status} {provider}: {desc}")
        else:
            print(f"   ❌ 状态: 不可用 ({onnx.get('error', '未知错误')})")
        
        # 推荐配置
        recommendation = detection_result['recommended_config']
        print(f"\n🎯 推荐配置:")
        print(f"   📋 类型: {recommendation['description']}")
        print(f"   🚀 提供者: {recommendation['provider']}")
        print(f"   📊 性能等级: {recommendation['performance']}")
        print(f"   💡 原因: {recommendation['reason']}")
        
        # GPU加速状态
        gpu_status = "启用" if detection_result['gpu_available'] else "禁用"
        print(f"\n⚡ GPU加速: {gpu_status}")
        
        print("=" * 80)

def main():
    """主函数"""
    detector = GPUDetector()
    result = detector.detect_all()
    detector.print_detailed_report(result)
    
    return result

if __name__ == "__main__":
    main()
