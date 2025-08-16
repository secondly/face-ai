#!/usr/bin/env python3
"""
复制InsightFace模型到项目目录
"""

import shutil
import os
from pathlib import Path

def copy_insightface_models():
    """从InsightFace目录复制模型到项目"""
    print("📋 复制InsightFace模型到项目...")
    print("=" * 50)
    
    # 项目模型目录
    project_root = Path(__file__).parent.parent
    models_dir = project_root / "models"
    models_dir.mkdir(exist_ok=True)
    
    # InsightFace模型目录
    insightface_root = Path.home() / '.insightface'
    
    print(f"📁 源目录: {insightface_root}")
    print(f"📁 目标目录: {models_dir}")
    
    if not insightface_root.exists():
        print("❌ InsightFace模型目录不存在")
        print("请先运行 download_buffalo_l.py 下载模型")
        return False
    
    # 文件映射 - 根据实际InsightFace buffalo_l模型包内容
    file_mapping = {
        # 目标文件名: [可能的源文件名列表]
        'scrfd_10g_bnkps.onnx': ['det_10g.onnx'],
        'arcface_r100.onnx': ['w600k_r50.onnx'],  # buffalo_l中的识别模型
        'inswapper_128.onnx': ['inswapper_128.onnx']
    }
    
    success_count = 0
    total_files = len(file_mapping)
    
    print(f"\n🔄 开始复制 {total_files} 个模型文件...")
    
    for target_name, source_names in file_mapping.items():
        target_path = models_dir / target_name
        
        if target_path.exists():
            size_mb = target_path.stat().st_size / (1024 * 1024)
            print(f"✅ {target_name} 已存在 ({size_mb:.1f}MB)")
            success_count += 1
            continue
        
        # 搜索源文件
        found = False
        print(f"🔍 查找 {target_name}...")
        
        for root, dirs, files in os.walk(insightface_root):
            for source_name in source_names:
                if source_name in files:
                    source_path = Path(root) / source_name
                    try:
                        print(f"📥 复制 {source_name} -> {target_name}")
                        shutil.copy2(source_path, target_path)
                        
                        # 验证复制结果
                        if target_path.exists():
                            size_mb = target_path.stat().st_size / (1024 * 1024)
                            print(f"✅ 复制成功 ({size_mb:.1f}MB)")
                            success_count += 1
                            found = True
                            break
                        else:
                            print(f"❌ 复制失败: 目标文件不存在")
                    except Exception as e:
                        print(f"❌ 复制失败: {e}")
            if found:
                break
        
        if not found:
            print(f"⚠️ 未找到 {target_name} 的源文件")
            print(f"   查找的文件名: {source_names}")
    
    print(f"\n📊 复制结果: {success_count}/{total_files} 个文件成功")
    
    if success_count >= 2:  # 至少需要2个核心模型
        print("✅ 核心模型文件已就绪")
        
        # 列出models目录中的所有文件
        print(f"\n📁 {models_dir} 目录内容:")
        for file_path in models_dir.glob("*.onnx"):
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ {file_path.name} ({size_mb:.1f}MB)")
        
        return True
    else:
        print("❌ 缺少必要的模型文件")
        return False

def list_insightface_models():
    """列出InsightFace目录中的所有模型"""
    print("\n🔍 InsightFace目录中的模型文件:")
    print("-" * 40)
    
    insightface_root = Path.home() / '.insightface'
    
    if not insightface_root.exists():
        print("❌ InsightFace目录不存在")
        return
    
    found_models = []
    for root, dirs, files in os.walk(insightface_root):
        for file in files:
            if file.endswith('.onnx'):
                file_path = Path(root) / file
                size_mb = file_path.stat().st_size / (1024 * 1024)
                rel_path = file_path.relative_to(insightface_root)
                found_models.append((str(rel_path), size_mb))
    
    if found_models:
        for model_path, size_mb in found_models:
            print(f"  📄 {model_path} ({size_mb:.1f}MB)")
    else:
        print("❌ 未找到任何.onnx模型文件")

def main():
    """主函数"""
    print("🚀 AI换脸工具 - 模型文件复制器")
    print("=" * 50)
    
    # 先列出可用的模型
    list_insightface_models()
    
    # 复制模型
    success = copy_insightface_models()
    
    if success:
        print("\n🎉 模型复制完成！")
        print("现在可以正常使用AI换脸工具了。")
        print("\n💡 下一步:")
        print("1. 关闭此窗口")
        print("2. 重新启动AI换脸工具")
        print("3. 检查是否还有其他配置问题")
    else:
        print("\n❌ 模型复制失败")
        print("请检查InsightFace模型是否正确下载")
    
    input("\n按回车键退出...")
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n用户取消操作")
        exit(1)
    except Exception as e:
        print(f"\n❌ 脚本执行失败: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
        exit(1)
