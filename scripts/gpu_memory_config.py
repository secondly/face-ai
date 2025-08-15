#!/usr/bin/env python3
"""
GPU内存配置工具
允许用户设置GPU内存使用限制
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_config():
    """加载GPU内存配置"""
    config_file = project_root / "config" / "gpu_memory.json"
    
    default_config = {
        "memory_limit_percent": 90,
        "memory_check_interval": 10,
        "auto_fallback_enabled": True,
        "max_gpu_errors": 5
    }
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"加载配置失败: {e}")
            return default_config
    else:
        return default_config

def save_config(config):
    """保存GPU内存配置"""
    config_file = project_root / "config" / "gpu_memory.json"
    config_file.parent.mkdir(exist_ok=True)
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False

def show_current_config():
    """显示当前配置"""
    config = load_config()
    
    print("🔧 当前GPU内存配置:")
    print("=" * 50)
    print(f"内存使用限制: {config['memory_limit_percent']}%")
    print(f"内存检查间隔: 每{config['memory_check_interval']}帧")
    print(f"自动回退: {'启用' if config['auto_fallback_enabled'] else '禁用'}")
    print(f"最大GPU错误次数: {config['max_gpu_errors']}次")
    print()

def configure_memory_limit():
    """配置内存使用限制"""
    config = load_config()
    
    print("🎯 配置GPU内存使用限制")
    print("=" * 50)
    print(f"当前限制: {config['memory_limit_percent']}%")
    print("建议设置:")
    print("  - 80%: 保守设置，适合多任务环境")
    print("  - 90%: 平衡设置，适合大多数情况")
    print("  - 95%: 激进设置，最大化GPU利用率")
    print()
    
    try:
        new_limit = input("请输入新的内存限制百分比 (50-98): ").strip()
        if new_limit:
            limit = int(new_limit)
            if 50 <= limit <= 98:
                config['memory_limit_percent'] = limit
                print(f"✅ 内存限制已设置为 {limit}%")
            else:
                print("❌ 无效范围，请输入50-98之间的数值")
                return False
    except ValueError:
        print("❌ 无效输入，请输入数字")
        return False
    
    return save_config(config)

def configure_check_interval():
    """配置内存检查间隔"""
    config = load_config()
    
    print("⏱️ 配置内存检查间隔")
    print("=" * 50)
    print(f"当前间隔: 每{config['memory_check_interval']}帧")
    print("建议设置:")
    print("  - 5帧: 频繁检查，响应快但开销大")
    print("  - 10帧: 平衡设置，适合大多数情况")
    print("  - 20帧: 较少检查，开销小但响应慢")
    print()
    
    try:
        new_interval = input("请输入新的检查间隔 (1-50帧): ").strip()
        if new_interval:
            interval = int(new_interval)
            if 1 <= interval <= 50:
                config['memory_check_interval'] = interval
                print(f"✅ 检查间隔已设置为每{interval}帧")
            else:
                print("❌ 无效范围，请输入1-50之间的数值")
                return False
    except ValueError:
        print("❌ 无效输入，请输入数字")
        return False
    
    return save_config(config)

def configure_auto_fallback():
    """配置自动回退"""
    config = load_config()
    
    print("🔄 配置自动回退")
    print("=" * 50)
    print(f"当前状态: {'启用' if config['auto_fallback_enabled'] else '禁用'}")
    print("说明:")
    print("  - 启用: GPU错误时自动切换到CPU模式")
    print("  - 禁用: GPU错误时停止处理")
    print()
    
    choice = input("是否启用自动回退? (y/n): ").strip().lower()
    if choice in ['y', 'yes', '是']:
        config['auto_fallback_enabled'] = True
        print("✅ 自动回退已启用")
    elif choice in ['n', 'no', '否']:
        config['auto_fallback_enabled'] = False
        print("✅ 自动回退已禁用")
    else:
        print("❌ 无效输入")
        return False
    
    return save_config(config)

def main():
    """主函数"""
    print("🎮 GPU内存配置工具")
    print("=" * 60)
    
    while True:
        show_current_config()
        
        print("请选择操作:")
        print("1. 配置内存使用限制")
        print("2. 配置内存检查间隔")
        print("3. 配置自动回退")
        print("4. 重置为默认配置")
        print("5. 退出")
        print()
        
        choice = input("请输入选项 (1-5): ").strip()
        
        if choice == '1':
            configure_memory_limit()
        elif choice == '2':
            configure_check_interval()
        elif choice == '3':
            configure_auto_fallback()
        elif choice == '4':
            # 重置配置
            default_config = {
                "memory_limit_percent": 90,
                "memory_check_interval": 10,
                "auto_fallback_enabled": True,
                "max_gpu_errors": 5
            }
            if save_config(default_config):
                print("✅ 配置已重置为默认值")
            else:
                print("❌ 重置配置失败")
        elif choice == '5':
            print("👋 再见!")
            break
        else:
            print("❌ 无效选项，请重新选择")
        
        print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        sys.exit(1)
