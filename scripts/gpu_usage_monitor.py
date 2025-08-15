#!/usr/bin/env python3
"""
实时GPU使用监控工具
在AI换脸过程中实时显示GPU使用情况
"""

import sys
import time
import threading
import subprocess
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class GPUMonitor:
    """GPU使用监控器"""
    
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.gpu_usage_history = []
        self.cpu_usage_history = []
    
    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print("🔍 GPU监控已启动...")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("⏹️ GPU监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        import psutil
        
        while self.monitoring:
            try:
                # 获取GPU使用率
                gpu_info = self._get_gpu_usage()
                
                # 获取CPU使用率
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                
                # 记录历史
                self.gpu_usage_history.append(gpu_info)
                self.cpu_usage_history.append(cpu_percent)
                
                # 保持历史记录在合理范围内
                if len(self.gpu_usage_history) > 30:
                    self.gpu_usage_history.pop(0)
                    self.cpu_usage_history.pop(0)
                
                # 显示当前状态
                self._display_status(gpu_info, cpu_percent, memory.percent)
                
                time.sleep(1)
                
            except Exception as e:
                print(f"监控错误: {e}")
                time.sleep(1)
    
    def _get_gpu_usage(self):
        """获取GPU使用情况"""
        try:
            # 尝试nvidia-smi
            result = subprocess.run([
                'nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,name', 
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpus = []
                for line in lines:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 4:
                        gpus.append({
                            'utilization': int(parts[0]) if parts[0].isdigit() else 0,
                            'memory_used': int(parts[1]) if parts[1].isdigit() else 0,
                            'memory_total': int(parts[2]) if parts[2].isdigit() else 0,
                            'name': parts[3]
                        })
                return {'type': 'nvidia', 'gpus': gpus}
        except:
            pass
        
        # 如果nvidia-smi不可用，返回默认信息
        return {'type': 'unknown', 'gpus': []}
    
    def _display_status(self, gpu_info, cpu_percent, memory_percent):
        """显示状态"""
        # 清屏并显示状态
        print("\033[2J\033[H", end="")  # 清屏
        
        print("🎯 AI换脸 GPU使用监控")
        print("=" * 60)
        
        # GPU状态
        if gpu_info['type'] == 'nvidia' and gpu_info['gpus']:
            for i, gpu in enumerate(gpu_info['gpus']):
                util = gpu['utilization']
                mem_used = gpu['memory_used']
                mem_total = gpu['memory_total']
                name = gpu['name']
                
                # 使用率条形图
                bar_length = 30
                filled_length = int(bar_length * util / 100)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                
                print(f"🎮 GPU {i}: {name}")
                print(f"   使用率: [{bar}] {util:3d}%")
                print(f"   显存:   {mem_used:4d}/{mem_total:4d}MB ({mem_used/mem_total*100:.1f}%)")
        else:
            print("🎮 GPU: 未检测到NVIDIA GPU或DirectML GPU")
        
        # CPU状态
        cpu_bar_length = 30
        cpu_filled_length = int(cpu_bar_length * cpu_percent / 100)
        cpu_bar = '█' * cpu_filled_length + '░' * (cpu_bar_length - cpu_filled_length)
        
        print(f"\n💻 CPU: [{cpu_bar}] {cpu_percent:5.1f}%")
        print(f"💾 内存: {memory_percent:5.1f}%")
        
        # 显示趋势
        if len(self.gpu_usage_history) > 5:
            print(f"\n📊 GPU使用趋势 (最近10秒):")
            if gpu_info['type'] == 'nvidia' and gpu_info['gpus']:
                recent_gpu = [g['gpus'][0]['utilization'] if g['gpus'] else 0 for g in self.gpu_usage_history[-10:]]
                trend_str = ''.join(['▁▂▃▄▅▆▇█'[min(7, max(0, int(u/12.5)))] for u in recent_gpu])
                print(f"   GPU: {trend_str}")
            
            recent_cpu = self.cpu_usage_history[-10:]
            cpu_trend_str = ''.join(['▁▂▃▄▅▆▇█'[min(7, max(0, int(c/12.5)))] for c in recent_cpu])
            print(f"   CPU: {cpu_trend_str}")
        
        print(f"\n⏰ 监控时间: {time.strftime('%H:%M:%S')}")
        print("💡 提示: 在AI换脸过程中，GPU使用率应该会明显上升")
        print("🔄 按 Ctrl+C 停止监控")


def main():
    """主函数"""
    print("🚀 AI换脸 GPU使用监控工具")
    print("=" * 60)
    print("此工具将实时监控GPU使用情况")
    print("请在另一个窗口运行AI换脸程序，观察GPU使用率变化")
    print("=" * 60)
    
    monitor = GPUMonitor()
    
    try:
        monitor.start_monitoring()
        
        # 保持程序运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n用户中断监控")
    finally:
        monitor.stop_monitoring()
        
        # 显示总结
        if monitor.gpu_usage_history:
            gpu_max = 0
            if monitor.gpu_usage_history and monitor.gpu_usage_history[0].get('gpus'):
                gpu_max = max([g['gpus'][0]['utilization'] if g['gpus'] else 0 for g in monitor.gpu_usage_history])
            
            cpu_max = max(monitor.cpu_usage_history) if monitor.cpu_usage_history else 0
            cpu_avg = sum(monitor.cpu_usage_history) / len(monitor.cpu_usage_history) if monitor.cpu_usage_history else 0
            
            print("\n📊 监控总结:")
            print(f"   GPU最高使用率: {gpu_max}%")
            print(f"   CPU最高使用率: {cpu_max:.1f}%")
            print(f"   CPU平均使用率: {cpu_avg:.1f}%")
            
            if gpu_max > 50:
                print("✅ GPU被充分利用!")
            elif gpu_max > 10:
                print("⚠️ GPU有一定使用，但可能不够充分")
            else:
                print("❌ GPU使用率很低，可能主要在使用CPU")


if __name__ == "__main__":
    main()
