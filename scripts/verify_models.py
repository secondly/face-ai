#!/usr/bin/env python3
"""
模型验证脚本

验证已下载的ONNX模型文件的完整性和可用性。
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import onnxruntime as ort
    import numpy as np
    from download_models import MODELS_CONFIG, calculate_sha256, format_size
except ImportError as e:
    print(f"导入错误: {e}")
    print("请先安装依赖: pip install onnxruntime numpy")
    sys.exit(1)

def check_onnxruntime_providers():
    """检查ONNX Runtime可用的执行提供者"""
    available_providers = ort.get_available_providers()
    print("ONNX Runtime 可用的执行提供者:")
    for provider in available_providers:
        print(f"  ✓ {provider}")
    
    if "CUDAExecutionProvider" in available_providers:
        print("✓ GPU加速可用")
        return True
    else:
        print("⚠ GPU加速不可用，将使用CPU")
        return False

def verify_file_integrity(file_path, expected_sha256):
    """验证文件完整性"""
    if not os.path.exists(file_path):
        return False, "文件不存在"
    
    actual_sha256 = calculate_sha256(file_path)
    if actual_sha256 == expected_sha256:
        return True, "SHA256验证通过"
    else:
        return False, f"SHA256不匹配\n期望: {expected_sha256}\n实际: {actual_sha256}"

def test_model_loading(file_path, providers=None):
    """测试模型加载"""
    if providers is None:
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    
    try:
        session = ort.InferenceSession(str(file_path), providers=providers)
        
        # 获取模型信息
        inputs = session.get_inputs()
        outputs = session.get_outputs()
        
        model_info = {
            "inputs": [(inp.name, inp.shape, inp.type) for inp in inputs],
            "outputs": [(out.name, out.shape, out.type) for out in outputs],
            "provider": session.get_providers()[0]
        }
        
        return True, model_info
        
    except Exception as e:
        return False, str(e)

def create_dummy_input(input_info):
    """创建模拟输入数据"""
    name, shape, dtype = input_info
    
    # 处理动态形状
    actual_shape = []
    for dim in shape:
        if isinstance(dim, str) or dim == -1:
            # 动态维度，使用默认值
            if "batch" in str(dim).lower():
                actual_shape.append(1)
            else:
                actual_shape.append(224)  # 默认尺寸
        else:
            actual_shape.append(dim)
    
    # 根据数据类型创建数组
    if "float" in dtype:
        return np.random.randn(*actual_shape).astype(np.float32)
    elif "int" in dtype:
        return np.random.randint(0, 255, actual_shape, dtype=np.int64)
    else:
        return np.random.randn(*actual_shape).astype(np.float32)

def test_model_inference(file_path, providers=None):
    """测试模型推理"""
    if providers is None:
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    
    try:
        session = ort.InferenceSession(str(file_path), providers=providers)
        
        # 创建模拟输入
        inputs = session.get_inputs()
        input_data = {}
        
        for inp in inputs:
            dummy_input = create_dummy_input((inp.name, inp.shape, inp.type))
            input_data[inp.name] = dummy_input
        
        # 执行推理
        outputs = session.run(None, input_data)
        
        return True, f"推理成功，输出形状: {[out.shape for out in outputs]}"
        
    except Exception as e:
        return False, str(e)

def verify_models(models_dir, models_list=None, test_inference=False):
    """验证模型文件"""
    models_dir = Path(models_dir)
    
    if models_list is None:
        models_list = list(MODELS_CONFIG.keys())
    
    print(f"验证模型目录: {models_dir}")
    print("=" * 80)
    
    # 检查ONNX Runtime
    gpu_available = check_onnxruntime_providers()
    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if gpu_available else ["CPUExecutionProvider"]
    
    print("\n" + "=" * 80)
    
    results = {}
    
    for model_name in models_list:
        if model_name not in MODELS_CONFIG:
            print(f"⚠ 跳过未知模型: {model_name}")
            continue
        
        config = MODELS_CONFIG[model_name]
        file_path = models_dir / model_name
        
        print(f"\n验证模型: {model_name}")
        print(f"描述: {config['description']}")
        print("-" * 60)
        
        result = {"name": model_name, "status": "unknown", "details": []}
        
        # 1. 检查文件存在性
        if not file_path.exists():
            print("✗ 文件不存在")
            result["status"] = "missing"
            result["details"].append("文件不存在")
            results[model_name] = result
            continue
        
        file_size = file_path.stat().st_size
        print(f"✓ 文件存在 ({format_size(file_size)})")
        result["details"].append(f"文件大小: {format_size(file_size)}")
        
        # 2. 验证文件完整性
        is_valid, msg = verify_file_integrity(file_path, config['sha256'])
        if is_valid:
            print(f"✓ {msg}")
            result["details"].append("SHA256验证通过")
        else:
            print(f"✗ {msg}")
            result["status"] = "corrupted"
            result["details"].append("SHA256验证失败")
            results[model_name] = result
            continue
        
        # 3. 测试模型加载
        is_loaded, load_info = test_model_loading(file_path, providers)
        if is_loaded:
            print("✓ 模型加载成功")
            print(f"  执行提供者: {load_info['provider']}")
            print(f"  输入数量: {len(load_info['inputs'])}")
            print(f"  输出数量: {len(load_info['outputs'])}")
            
            result["details"].append(f"执行提供者: {load_info['provider']}")
            result["details"].append(f"输入/输出: {len(load_info['inputs'])}/{len(load_info['outputs'])}")
            
            # 显示输入输出详情
            for i, (name, shape, dtype) in enumerate(load_info['inputs']):
                print(f"  输入{i+1}: {name} {shape} ({dtype})")
            
        else:
            print(f"✗ 模型加载失败: {load_info}")
            result["status"] = "load_failed"
            result["details"].append(f"加载失败: {load_info}")
            results[model_name] = result
            continue
        
        # 4. 测试推理 (可选)
        if test_inference:
            print("  测试推理...")
            is_inferred, infer_info = test_model_inference(file_path, providers)
            if is_inferred:
                print(f"  ✓ {infer_info}")
                result["details"].append("推理测试通过")
                result["status"] = "ok"
            else:
                print(f"  ✗ 推理失败: {infer_info}")
                result["status"] = "inference_failed"
                result["details"].append(f"推理失败: {infer_info}")
        else:
            result["status"] = "ok"
        
        results[model_name] = result
    
    # 输出总结
    print("\n" + "=" * 80)
    print("验证结果总结:")
    
    status_counts = {"ok": 0, "missing": 0, "corrupted": 0, "load_failed": 0, "inference_failed": 0}
    
    for model_name, result in results.items():
        status = result["status"]
        status_counts[status] += 1
        
        if status == "ok":
            print(f"✓ {model_name}: 正常")
        elif status == "missing":
            print(f"✗ {model_name}: 文件缺失")
        elif status == "corrupted":
            print(f"✗ {model_name}: 文件损坏")
        elif status == "load_failed":
            print(f"✗ {model_name}: 加载失败")
        elif status == "inference_failed":
            print(f"⚠ {model_name}: 推理失败")
    
    print(f"\n统计: 正常({status_counts['ok']}) 缺失({status_counts['missing']}) "
          f"损坏({status_counts['corrupted']}) 加载失败({status_counts['load_failed']}) "
          f"推理失败({status_counts['inference_failed']})")
    
    total_ok = status_counts['ok'] + status_counts['inference_failed']  # 推理失败但加载成功也算基本可用
    total_models = len(results)
    
    if total_ok == total_models:
        print("✓ 所有模型验证通过！")
        return True
    else:
        print(f"✗ {total_models - total_ok} 个模型存在问题")
        return False

def main():
    parser = argparse.ArgumentParser(description="验证Deep-Live-Cam模型文件")
    parser.add_argument("--models-dir", default=str(PROJECT_ROOT / "models"),
                       help="模型目录 (默认: ./models)")
    parser.add_argument("--models", nargs="+",
                       help="指定要验证的模型 (默认: 验证所有模型)")
    parser.add_argument("--test-inference", action="store_true",
                       help="测试模型推理 (较慢但更全面)")
    
    args = parser.parse_args()
    
    success = verify_models(
        models_dir=args.models_dir,
        models_list=args.models,
        test_inference=args.test_inference
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
