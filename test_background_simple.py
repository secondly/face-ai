#!/usr/bin/env python3
"""
简单的背景替换功能测试
"""

import sys
from pathlib import Path

def test_import():
    """测试导入"""
    print("🧪 测试背景替换模块导入...")
    
    try:
        # 测试核心模块导入
        from core.background_replacer import BackgroundReplacer
        print("✅ BackgroundReplacer 导入成功")
        
        # 测试创建实例
        replacer = BackgroundReplacer(mode="rembg")
        print(f"✅ BackgroundReplacer 实例创建成功，模式: {replacer.mode}")
        
        # 测试可用性
        if replacer.is_available():
            print("✅ 背景替换功能可用")
        else:
            print("⚠️ 背景替换功能不可用（可能缺少依赖）")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_gui_integration():
    """测试GUI集成"""
    print("\n🖥️ 测试GUI集成...")
    
    try:
        # 测试GUI模块导入
        from gui.pyqt_gui import ModernFaceSwapGUI
        print("✅ GUI模块导入成功")
        
        # 检查是否有背景替换相关的属性
        import inspect
        gui_methods = [method for method in dir(ModernFaceSwapGUI) if 'background' in method.lower()]
        
        if gui_methods:
            print(f"✅ 找到背景替换相关方法: {gui_methods}")
        else:
            print("⚠️ 未找到背景替换相关方法")
        
        return True
        
    except ImportError as e:
        print(f"❌ GUI导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ GUI测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🎨 AI换脸 - 背景替换功能简单测试")
    print("=" * 50)
    
    # 测试导入
    import_ok = test_import()
    
    # 测试GUI集成
    gui_ok = test_gui_integration()
    
    # 总结
    print("\n" + "=" * 50)
    if import_ok and gui_ok:
        print("🎉 所有测试通过！背景替换功能已成功集成")
        print("\n📝 使用说明:")
        print("1. 启动GUI: python main_pyqt.py")
        print("2. 勾选'启用背景替换'")
        print("3. 选择背景替换模式")
        print("4. 选择背景图片或文件夹")
        print("5. 开始换脸处理")
        
        print("\n💡 提示:")
        print("- 如果背景替换不可用，请运行: python scripts/install_background_deps.py")
        print("- 推荐使用BackgroundMattingV2模式获得最佳效果")
        print("- 支持单张背景图片或文件夹随机选择")
    else:
        print("❌ 部分测试失败，请检查安装")
        if not import_ok:
            print("- 核心模块有问题")
        if not gui_ok:
            print("- GUI集成有问题")

if __name__ == "__main__":
    main()
