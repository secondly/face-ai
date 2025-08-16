#!/usr/bin/env python3
"""
专门下载buffalo_l模型的脚本
"""

import sys
import os
from pathlib import Path

def download_buffalo_l():
    """下载buffalo_l模型"""
    print("🤖 开始下载buffalo_l模型...")
    print("=" * 50)
    
    try:
        # 检查InsightFace是否已安装
        print("📦 检查InsightFace...")
        try:
            import insightface
            print("✅ InsightFace已安装")
        except ImportError:
            print("❌ InsightFace未安装，正在安装...")
            import subprocess
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'insightface'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ InsightFace安装失败: {result.stderr}")
                return False
            print("✅ InsightFace安装成功")
            import insightface
        
        # 下载buffalo_l模型
        print("\n📥 下载buffalo_l模型包...")
        print("这可能需要几分钟时间，请耐心等待...")
        
        try:
            # 创建FaceAnalysis实例会自动下载buffalo_l模型
            # 现在ONNX Runtime 1.19.2应该支持GPU模式了
            print("尝试使用GPU模式下载...")
            try:
                app = insightface.app.FaceAnalysis(name='buffalo_l')
                print("✅ GPU模式成功")
            except Exception as e:
                print(f"⚠️ GPU模式失败，切换到CPU模式: {e}")
                app = insightface.app.FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
            print("✅ buffalo_l模型包下载成功")

            # 初始化模型（这会确保模型完全可用）
            print("🔧 初始化模型...")
            app.prepare(ctx_id=-1, det_size=(640, 640))
            print("✅ 模型初始化成功")
            
            # 检查模型文件位置
            insightface_root = Path.home() / '.insightface'
            print(f"\n📁 模型文件位置: {insightface_root}")
            
            # 列出下载的文件
            if insightface_root.exists():
                print("📋 已下载的模型文件:")
                for root, dirs, files in os.walk(insightface_root):
                    for file in files:
                        if file.endswith('.onnx'):
                            file_path = Path(root) / file
                            size_mb = file_path.stat().st_size / (1024 * 1024)
                            print(f"  ✅ {file} ({size_mb:.1f}MB)")
            
            print("\n🎉 buffalo_l模型下载完成！")
            print("现在可以正常使用AI换脸功能了。")
            return True
            
        except Exception as e:
            print(f"❌ buffalo_l模型下载失败: {e}")
            print("\n💡 可能的解决方案:")
            print("1. 检查网络连接")
            print("2. 尝试使用VPN")
            print("3. 重新运行此脚本")
            return False
            
    except Exception as e:
        print(f"❌ 下载过程出错: {e}")
        return False

def main():
    """主函数"""
    print("🚀 AI换脸工具 - buffalo_l模型下载器")
    print("=" * 50)
    
    success = download_buffalo_l()
    
    if success:
        print("\n✅ 下载完成！")
        print("现在可以关闭此窗口并重新启动AI换脸工具。")
    else:
        print("\n❌ 下载失败")
        print("请检查网络连接后重试，或联系技术支持。")
    
    input("\n按回车键退出...")
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n用户取消下载")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 脚本执行失败: {e}")
        input("\n按回车键退出...")
        sys.exit(1)
