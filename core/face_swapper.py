"""
核心换脸引擎
使用InsightFace进行人脸检测、识别和换脸
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple, Union
import logging
import subprocess
import os
import platform

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FaceSwapper:
    """核心换脸引擎"""
    
    def __init__(self, models_dir: str = "models", use_gpu: bool = True):
        """
        初始化换脸引擎

        Args:
            models_dir: 模型文件目录
            use_gpu: 是否使用GPU加速
        """
        self.models_dir = Path(models_dir)
        self.use_gpu = use_gpu
        self.face_analyser = None
        self.face_swapper = None

        # 错误计数器，用于自动回退
        self.gpu_error_count = 0
        self.max_gpu_errors = 5  # 连续5次GPU错误后回退到CPU
        self.fallback_to_cpu = False

        # GPU内存管理 - 从配置文件加载
        self._load_gpu_memory_config()

        # 帧计数器，用于控制内存检查频率
        self.frame_count = 0

        # 检测GPU环境
        self.providers = self._get_providers()
        print(f"使用推理提供者: {self.providers}")  # 使用print避免线程问题

        self._initialize_models()

    def cleanup_gpu_memory(self):
        """清理GPU内存（安全版本，避免崩溃）"""
        try:
            # 只清理GPU缓存，不删除模型对象（避免崩溃）
            import gc
            gc.collect()

            # 如果使用CUDA，清理CUDA缓存
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    logger.info("已清理CUDA缓存")
            except ImportError:
                pass

            logger.info("GPU内存清理完成")

        except Exception as e:
            logger.error(f"GPU内存清理失败: {e}")

    def force_cleanup_models(self):
        """强制清理模型（仅在程序退出时使用）"""
        try:
            # 清理人脸分析器
            if hasattr(self, 'face_analyser') and self.face_analyser is not None:
                try:
                    del self.face_analyser
                    self.face_analyser = None
                    logger.info("已清理人脸分析器")
                except Exception as e:
                    logger.warning(f"清理人脸分析器失败: {e}")

            # 清理换脸模型
            if hasattr(self, 'face_swapper') and self.face_swapper is not None:
                try:
                    del self.face_swapper
                    self.face_swapper = None
                    logger.info("已清理换脸模型")
                except Exception as e:
                    logger.warning(f"清理换脸模型失败: {e}")

            # 强制垃圾回收
            import gc
            gc.collect()

            # 如果使用DirectML，尝试清理
            try:
                import onnxruntime as ort
                # DirectML没有直接的清理方法，但删除会话会释放内存
                logger.info("已清理ONNX Runtime会话")
            except ImportError:
                pass

            logger.info("GPU内存清理完成")

        except Exception as e:
            logger.error(f"GPU内存清理失败: {e}")

    def _load_gpu_memory_config(self):
        """加载GPU内存配置"""
        try:
            import json
            config_file = Path(__file__).parent.parent / "config" / "gpu_memory.json"

            # 默认配置
            default_config = {
                "memory_limit_percent": 90,
                "memory_check_interval": 10,
                "auto_fallback_enabled": True,
                "max_gpu_errors": 5
            }

            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
            else:
                config = default_config

            # 应用配置
            self.gpu_memory_limit_percent = config['memory_limit_percent']
            self.gpu_memory_check_interval = config['memory_check_interval']
            self.auto_fallback_enabled = config['auto_fallback_enabled']
            self.max_gpu_errors = config['max_gpu_errors']

            logger.info(f"GPU内存配置: 限制{self.gpu_memory_limit_percent}%, 检查间隔{self.gpu_memory_check_interval}帧")

        except Exception as e:
            logger.warning(f"加载GPU内存配置失败，使用默认值: {e}")
            # 使用默认值
            self.gpu_memory_limit_percent = 90
            self.gpu_memory_check_interval = 10
            self.auto_fallback_enabled = True
            self.max_gpu_errors = 5

    def _check_gpu_memory_usage(self) -> tuple[bool, float]:
        """
        检查GPU内存使用情况
        返回: (是否可以使用GPU, 当前使用率)
        """
        try:
            from utils.system_monitor import SystemMonitor
            monitor = SystemMonitor()
            gpu_info = monitor.get_gpu_info()

            if gpu_info.get('available') and gpu_info.get('gpus'):
                gpu = gpu_info['gpus'][0]
                memory_used_mb = gpu['memory_used_mb']
                memory_total_mb = gpu['memory_total_mb']

                usage_percent = (memory_used_mb / memory_total_mb) * 100

                # 根据使用率决定策略
                if usage_percent > self.gpu_memory_limit_percent:
                    logger.warning(f"GPU内存使用率 {usage_percent:.1f}% 超过限制 {self.gpu_memory_limit_percent}%，临时使用CPU")
                    return False, usage_percent
                elif usage_percent > (self.gpu_memory_limit_percent - 10):
                    logger.info(f"GPU内存使用率 {usage_percent:.1f}% 接近限制，谨慎使用GPU")
                    return True, usage_percent
                else:
                    logger.debug(f"GPU内存使用率: {usage_percent:.1f}%，正常使用GPU")
                    return True, usage_percent

            return True, 0.0  # 如果无法检测，默认允许使用

        except Exception as e:
            logger.debug(f"GPU内存检查失败: {e}")
            return True, 0.0  # 检查失败时默认允许使用

    def _get_providers(self):
        """获取可用的推理提供者"""
        providers = []

        if self.use_gpu:
            try:
                import onnxruntime as ort
                available_providers = ort.get_available_providers()
                print(f"可用的ONNX提供者: {available_providers}")

                # 对于NVIDIA MX230等较老GPU，优先使用DirectML
                if 'DmlExecutionProvider' in available_providers:
                    providers.append('DmlExecutionProvider')
                    print("检测到DirectML GPU，将使用GPU加速 (推荐用于NVIDIA MX系列)")
                elif 'CUDAExecutionProvider' in available_providers:
                    # 尝试CUDA，但可能在较老GPU上有兼容性问题
                    try:
                        # 简单测试CUDA是否真正可用
                        test_session = ort.InferenceSession(
                            # 创建一个最小的测试模型
                            b'\x08\x01\x12\x0c\x08\x01\x12\x08\x08\x01\x12\x04\x08\x01\x10\x01',
                            providers=['CUDAExecutionProvider']
                        )
                        providers.append('CUDAExecutionProvider')
                        print("检测到CUDA GPU，将使用GPU加速")
                    except:
                        print("CUDA GPU检测失败，回退到DirectML")
                        if 'DmlExecutionProvider' in available_providers:
                            providers.append('DmlExecutionProvider')
                        else:
                            providers.append('CPUExecutionProvider')
                else:
                    print("未检测到GPU支持，将使用CPU")
                    print("提示: 如需GPU加速，请安装 onnxruntime-gpu 或 onnxruntime-directml")
                    providers.append('CPUExecutionProvider')
            except ImportError:
                print("ONNX Runtime未安装，将使用CPU")
                providers.append('CPUExecutionProvider')
        else:
            print("手动指定使用CPU")
            providers.append('CPUExecutionProvider')

        return providers

    def _initialize_models(self):
        """初始化模型"""
        try:
            import insightface

            # 初始化人脸分析器 (检测 + 识别)
            logger.info("正在初始化人脸分析器...")
            self.face_analyser = insightface.app.FaceAnalysis(
                name='buffalo_l',
                providers=self.providers
            )
            # 设置GPU上下文ID - DirectML和CUDA都使用0，CPU使用-1
            ctx_id = 0 if ('CUDAExecutionProvider' in self.providers or 'DmlExecutionProvider' in self.providers) else -1
            print(f"设置上下文ID: {ctx_id} (providers: {self.providers})")
            self.face_analyser.prepare(ctx_id=ctx_id, det_size=(640, 640))

            # 手动设置所有模型的providers (确保GPU被正确使用)
            print("为FaceAnalysis中的所有模型设置providers...")
            for task_name, model in self.face_analyser.models.items():
                if hasattr(model, 'session'):
                    try:
                        model.session.set_providers(self.providers)
                        actual_providers = model.session.get_providers()
                        print(f"  {task_name} 模型使用providers: {actual_providers}")
                    except Exception as e:
                        print(f"  {task_name} 模型设置providers失败: {e}")

            # 初始化换脸模型
            logger.info("正在初始化换脸模型...")

            # 确保项目模型文件存在并复制到InsightFace目录
            inswapper_path = self.models_dir / "inswapper_128.onnx"
            if inswapper_path.exists():
                logger.info(f"找到项目模型文件: {inswapper_path}")

                # 确保InsightFace目录存在
                import shutil
                insightface_models_dir = Path.home() / '.insightface' / 'models'
                insightface_models_dir.mkdir(parents=True, exist_ok=True)
                insightface_inswapper = insightface_models_dir / "inswapper_128.onnx"

                # 复制模型文件到InsightFace目录
                if not insightface_inswapper.exists():
                    logger.info("复制模型到InsightFace目录...")
                    shutil.copy2(inswapper_path, insightface_inswapper)

                # 验证文件是否复制成功
                if not insightface_inswapper.exists():
                    raise FileNotFoundError(f"模型复制失败: {insightface_inswapper}")

                # 加载模型 - 使用完整路径并指定providers
                from insightface.model_zoo import get_model
                try:
                    self.face_swapper = get_model('inswapper_128.onnx', download=False)
                    # 手动设置providers (InsightFace可能不会自动使用)
                    if hasattr(self.face_swapper, 'session'):
                        print(f"为INSwapper设置providers: {self.providers}")
                        self.face_swapper.session.set_providers(self.providers)
                except:
                    # 如果还是失败，尝试直接指定路径
                    import onnxruntime as ort
                    from insightface.model_zoo.inswapper import INSwapper

                    # 创建带有指定providers的ONNX会话
                    session = ort.InferenceSession(str(insightface_inswapper), providers=self.providers)
                    print(f"INSwapper使用providers: {session.get_providers()}")

                    self.face_swapper = INSwapper(model_file=str(insightface_inswapper), session=session)
                logger.info("inswapper模型加载成功")
            else:
                raise FileNotFoundError(f"inswapper模型文件不存在: {inswapper_path}\n请运行: python scripts/simple_model_getter.py")

            logger.info("模型初始化完成")

        except Exception as e:
            logger.error(f"❌ 模型初始化失败: {e}")
            raise
    
    def get_faces(self, image: np.ndarray) -> List:
        """
        检测图像中的人脸

        Args:
            image: 输入图像 (BGR格式)

        Returns:
            人脸列表，每个人脸包含关键点、边界框、特征等信息
        """
        if self.face_analyser is None:
            # 尝试重新初始化人脸分析器
            logger.warning("人脸分析器未初始化，尝试重新初始化...")
            try:
                self._initialize_models()
                logger.info("人脸分析器重新初始化成功")
            except Exception as e:
                logger.error(f"重新初始化人脸分析器失败: {e}")
                raise RuntimeError("人脸分析器未初始化且重新初始化失败")

        # 如果使用GPU，按间隔检查内存使用情况
        if 'DmlExecutionProvider' in self.providers or 'CUDAExecutionProvider' in self.providers:
            self.frame_count += 1

            # 每隔指定帧数检查一次内存
            if self.frame_count % self.gpu_memory_check_interval == 0:
                can_use_gpu, memory_usage = self._check_gpu_memory_usage()

                if not can_use_gpu:
                    logger.warning(f"GPU内存使用率 {memory_usage:.1f}% 过高，临时使用CPU模式")
                    # 临时使用CPU处理这一帧
                    try:
                        import insightface
                        temp_analyser = insightface.app.FaceAnalysis(
                            name='buffalo_l',
                            providers=['CPUExecutionProvider']
                        )
                        temp_analyser.prepare(ctx_id=-1, det_size=(640, 640))
                        faces = temp_analyser.get(image)
                        logger.info(f"临时CPU模式检测到 {len(faces)} 个人脸 (GPU内存: {memory_usage:.1f}%)")
                        return faces
                    except Exception as cpu_error:
                        logger.error(f"临时CPU模式失败: {cpu_error}")
                        # 继续尝试GPU模式
                elif memory_usage > (self.gpu_memory_limit_percent - 10):
                    logger.debug(f"GPU内存使用率 {memory_usage:.1f}% 接近限制，继续使用GPU但需谨慎")

        try:
            faces = self.face_analyser.get(image)
            # 成功时重置错误计数
            self.gpu_error_count = 0
            return faces
        except Exception as e:
            # 详细记录错误信息
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"人脸检测失败: {e}")
            logger.error(f"详细错误: {error_details}")

            # 检查是否是ONNX Runtime错误
            if "onnxruntime" in str(e).lower() or "fail" in str(e).lower():
                self.gpu_error_count += 1
                logger.warning(f"检测到ONNX Runtime错误 (第{self.gpu_error_count}次)，可能是GPU内存不足或驱动问题")

                # 检查是否是GPU内存相关错误，如果是则立即切换到CPU
                is_memory_error = any(keyword in str(e).lower() for keyword in [
                    'memory', 'out of memory', 'cuda', 'directml', 'gpu'
                ])

                # 如果是内存错误或错误次数过多，永久切换到CPU模式
                if (is_memory_error or self.gpu_error_count >= self.max_gpu_errors) and not self.fallback_to_cpu:
                    reason = "GPU内存不足" if is_memory_error else f"GPU错误次数达到{self.max_gpu_errors}次"
                    logger.warning(f"{reason}，永久切换到CPU模式")
                    self.fallback_to_cpu = True

                    try:
                        # 重新初始化为CPU模式
                        import insightface
                        logger.info("正在重新初始化为CPU模式...")
                        self.face_analyser = insightface.app.FaceAnalysis(
                            name='buffalo_l',
                            providers=['CPUExecutionProvider']
                        )
                        self.face_analyser.prepare(ctx_id=-1, det_size=(640, 640))
                        self.providers = ['CPUExecutionProvider']
                        logger.info("已成功切换到CPU模式")

                        # 重新尝试检测
                        faces = self.face_analyser.get(image)
                        logger.info(f"CPU模式成功检测到 {len(faces)} 个人脸")
                        return faces

                    except Exception as cpu_error:
                        logger.error(f"CPU模式初始化失败: {cpu_error}")

                # 如果已经是CPU模式，直接返回空结果
                elif self.fallback_to_cpu:
                    logger.warning("已在CPU模式下，但仍然检测失败")
                    return []

                # 临时回退到CPU处理这一帧
                else:
                    logger.info("尝试临时使用CPU模式处理此帧...")
                    try:
                        # 创建临时的CPU分析器
                        import insightface
                        temp_analyser = insightface.app.FaceAnalysis(
                            name='buffalo_l',
                            providers=['CPUExecutionProvider']
                        )
                        temp_analyser.prepare(ctx_id=-1, det_size=(640, 640))

                        # 使用CPU模式检测
                        faces = temp_analyser.get(image)
                        logger.info(f"临时CPU模式成功检测到 {len(faces)} 个人脸")
                        return faces

                    except Exception as cpu_error:
                        logger.error(f"临时CPU模式也失败: {cpu_error}")

            return []

    def get_faces_with_info(self, image: np.ndarray) -> List[dict]:
        """
        检测图像中的人脸并返回详细信息

        Args:
            image: 输入图像 (BGR格式)

        Returns:
            包含人脸信息的列表 [{'face': face, 'bbox': bbox, 'area': area, 'center': center}]
        """
        try:
            faces = self.get_faces(image)
            face_info_list = []

            for i, face in enumerate(faces):
                bbox = face.bbox.astype(int)  # [x1, y1, x2, y2]
                area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                center = ((bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2)

                # 获取人脸特征向量
                embedding = None
                try:
                    embedding = face.embedding if hasattr(face, 'embedding') else None
                except:
                    embedding = None

                face_info = {
                    'index': i,
                    'face': face,
                    'bbox': bbox,
                    'area': area,
                    'center': center,
                    'confidence': getattr(face, 'det_score', 0.0),
                    'embedding': embedding
                }
                face_info_list.append(face_info)

            # 按人脸大小排序（大的在前）
            face_info_list.sort(key=lambda x: x['area'], reverse=True)

            return face_info_list
        except Exception as e:
            # 详细记录错误信息
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"人脸检测失败: {e}")
            logger.error(f"详细错误: {error_details}")

            # 如果是GPU相关错误，尝试回退到CPU
            if "DirectML" in str(e) or "DML" in str(e) or "GPU" in str(e):
                logger.warning("检测到GPU相关错误，尝试回退到CPU模式")
                try:
                    # 使用CPU模式重新检测
                    faces = self.get_faces(image)  # 这会触发上面的CPU回退逻辑

                    # 如果成功，重新构建face_info_list
                    if faces:
                        face_info_list = []
                        for i, face in enumerate(faces):
                            bbox = face.bbox.astype(int)
                            area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])

                            face_info = {
                                'face': face,
                                'bbox': bbox,
                                'area': area,
                                'confidence': getattr(face, 'det_score', 0.0),
                                'index': i
                            }
                            face_info_list.append(face_info)

                        # 按人脸大小排序
                        face_info_list.sort(key=lambda x: x['area'], reverse=True)
                        logger.info(f"CPU模式检测成功，找到 {len(face_info_list)} 个人脸")
                        return face_info_list

                except Exception as cpu_error:
                    logger.error(f"CPU模式也失败: {cpu_error}")

            return []

    def extract_face_preview(self, image: np.ndarray, face_info: dict, size: tuple = (150, 150)) -> Optional[np.ndarray]:
        """
        提取人脸预览图

        Args:
            image: 原始图像
            face_info: 人脸信息字典
            size: 预览图大小

        Returns:
            人脸预览图 (RGB格式)
        """
        try:
            bbox = face_info['bbox']
            x1, y1, x2, y2 = bbox

            # 扩展边界框以包含更多上下文
            margin = 20
            h, w = image.shape[:2]
            x1 = max(0, x1 - margin)
            y1 = max(0, y1 - margin)
            x2 = min(w, x2 + margin)
            y2 = min(h, y2 + margin)

            # 提取人脸区域
            face_crop = image[y1:y2, x1:x2]

            # 调整大小
            face_resized = cv2.resize(face_crop, size)

            # 转换为RGB
            face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)

            return face_rgb
        except Exception as e:
            logger.error(f"提取人脸预览失败: {e}")
            return None

    def get_face_embedding(self, image: np.ndarray, face=None) -> Optional[np.ndarray]:
        """
        获取人脸特征向量
        
        Args:
            image: 输入图像
            face: 人脸信息，如果为None则自动检测第一个人脸
            
        Returns:
            人脸特征向量
        """
        if face is None:
            faces = self.get_faces(image)
            if not faces:
                return None
            face = faces[0]
        
        return face.embedding if hasattr(face, 'embedding') else face.get('embedding')
    
    def swap_face(self, source_image: np.ndarray, target_image: np.ndarray, 
                  source_face=None, target_face=None) -> Optional[np.ndarray]:
        """
        执行人脸替换
        
        Args:
            source_image: 源人脸图像
            target_image: 目标图像
            source_face: 源人脸信息，如果为None则自动检测
            target_face: 目标人脸信息，如果为None则自动检测
            
        Returns:
            换脸后的图像
        """
        try:
            # 检测源人脸
            if source_face is None:
                source_faces = self.get_faces(source_image)
                if not source_faces:
                    logger.warning("源图像中未检测到人脸")
                    return None
                source_face = source_faces[0]
            
            # 检测目标人脸
            if target_face is None:
                target_faces = self.get_faces(target_image)
                if not target_faces:
                    logger.warning("目标图像中未检测到人脸")
                    return None
                target_face = target_faces[0]
            
            # 执行换脸
            result_image = target_image.copy()

            # 使用InsightFace的换脸功能
            try:
                # 使用inswapper模型进行换脸
                logger.debug(f"调用face_swapper.get: target_face={type(target_face)}, source_face={type(source_face)}")
                result_image = self.face_swapper.get(result_image, target_face, source_face, paste_back=True)
                logger.debug("换脸调用成功")
            except Exception as e:
                logger.error(f"换脸失败: {e}")
                return None
            
            return result_image
        except Exception as e:
            logger.error(f"换脸处理失败: {e}")
            return None

    def swap_face_selective(self, source_image: np.ndarray, target_image: np.ndarray,
                           target_face_index: int = 0) -> Optional[np.ndarray]:
        """
        选择性换脸 - 只替换指定索引的人脸

        Args:
            source_image: 源人脸图像
            target_image: 目标图像
            target_face_index: 要替换的目标人脸索引

        Returns:
            换脸后的图像，失败返回None
        """
        try:
            # 获取源人脸
            source_faces = self.get_faces(source_image)
            if not source_faces:
                logger.error("源图像中未检测到人脸")
                return None

            source_face = source_faces[0]  # 使用第一个检测到的人脸

            # 获取目标人脸信息
            target_face_info_list = self.get_faces_with_info(target_image)
            if not target_face_info_list:
                logger.error("目标图像中未检测到人脸")
                return None

            if target_face_index >= len(target_face_info_list):
                logger.error(f"目标人脸索引 {target_face_index} 超出范围，共检测到 {len(target_face_info_list)} 个人脸")
                return None

            # 获取指定的目标人脸
            target_face_info = target_face_info_list[target_face_index]
            target_face = target_face_info['face']

            # 执行换脸
            result_image = self.swap_face(source_face, target_image, target_face)

            return result_image

        except Exception as e:
            logger.error(f"选择性换脸失败: {e}")
            return None

    def find_matching_face(self, target_faces, reference_face_info, similarity_threshold=0.4, frame_count=None, total_frames=None):
        """
        在目标人脸列表中找到与参考人脸最匹配的人脸

        Args:
            target_faces: 目标帧中检测到的人脸列表
            reference_face_info: 参考人脸信息（包含位置、大小等）
            similarity_threshold: 相似度阈值
            frame_count: 当前帧数（用于日志）

        Returns:
            匹配的人脸索引，如果没有找到返回None
        """
        if not target_faces or not reference_face_info:
            return None

        try:
            ref_center = reference_face_info['center']
            ref_area = reference_face_info['area']

            best_match_index = None
            best_score = 0
            similarities = []  # 存储所有相似度

            for i, face in enumerate(target_faces):
                # 计算当前人脸信息
                bbox = face.bbox.astype(int)
                center = ((bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2)
                area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])

                # 计算人脸特征相似度（最重要）
                face_similarity = 0
                try:
                    # 获取当前人脸的特征向量
                    current_embedding = face.embedding if hasattr(face, 'embedding') else None
                    ref_embedding = reference_face_info.get('embedding')

                    if current_embedding is not None and ref_embedding is not None:
                        # 计算余弦相似度
                        import numpy as np
                        dot_product = np.dot(current_embedding, ref_embedding)
                        norm_current = np.linalg.norm(current_embedding)
                        norm_ref = np.linalg.norm(ref_embedding)

                        if norm_current > 0 and norm_ref > 0:
                            face_similarity = dot_product / (norm_current * norm_ref)
                            face_similarity = (face_similarity + 1) / 2  # 转换到0-1范围
                except:
                    face_similarity = 0

                # 计算位置相似度（距离越近越相似）
                distance = ((center[0] - ref_center[0]) ** 2 + (center[1] - ref_center[1]) ** 2) ** 0.5
                max_distance = (ref_center[0] ** 2 + ref_center[1] ** 2) ** 0.5  # 图像对角线长度的一半
                position_similarity = max(0, 1 - distance / max_distance) if max_distance > 0 else 0

                # 计算大小相似度
                area_ratio = min(area, ref_area) / max(area, ref_area) if max(area, ref_area) > 0 else 0

                # 综合相似度（人脸特征权重0.8，位置权重0.15，大小权重0.05）
                if face_similarity > 0:
                    total_similarity = face_similarity * 0.8 + position_similarity * 0.15 + area_ratio * 0.05
                else:
                    # 如果没有人脸特征，降级使用位置和大小
                    total_similarity = position_similarity * 0.7 + area_ratio * 0.3
                similarities.append(int(total_similarity * 100))  # 转换为百分比

                if total_similarity > best_score and total_similarity >= similarity_threshold:
                    best_score = total_similarity
                    best_match_index = i

            # 记录匹配度日志
            if frame_count is not None:  # 每1帧记录一次
                similarities_str = "，".join([str(s) for s in similarities])
                max_similarity = max(similarities) if similarities else 0

                if best_match_index is not None:
                    msg = f"帧 {frame_count}: 检测到{len(target_faces)}个人脸，匹配度：【{similarities_str}】，选择人脸{best_match_index+1}({similarities[best_match_index]}%)"
                    logger.info(msg)
                    # 通过进度回调发送到GUI
                    if hasattr(self, 'progress_callback') and self.progress_callback:
                        progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                        # 发送匹配度信息，但不发送预览图像（避免每帧都发送）
                        self.progress_callback(progress, frame_count, total_frames, msg)
                else:
                    msg = f"帧 {frame_count}: 检测到{len(target_faces)}个人脸，匹配度：【{similarities_str}】，无匹配人脸"
                    logger.info(msg)
                    # 通过进度回调发送到GUI
                    if hasattr(self, 'progress_callback') and self.progress_callback:
                        progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                        self.progress_callback(progress, frame_count, total_frames, msg)

                    # 如果匹配度太低，给出建议
                    if max_similarity < 40:
                        if frame_count == 0:  # 只在第一次记录建议
                            warning_msg = f"⚠️ 匹配度过低({max_similarity}%)，建议检查参考人脸是否正确"
                            logger.warning(warning_msg)
                            if hasattr(self, 'progress_callback') and self.progress_callback:
                                progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                                self.progress_callback(progress, frame_count, total_frames, warning_msg)

            return best_match_index

        except Exception as e:
            logger.error(f"人脸匹配失败: {e}")
            return None

    def warm_up_models(self):
        """
        预热模型 - 提高后续处理速度
        """
        try:
            logger.info("开始预热模型...")

            # 创建测试图像
            test_image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)

            # 预热人脸检测
            self.get_faces(test_image)

            # 预热换脸模型（如果有检测到的人脸）
            faces = self.get_faces(test_image)
            if faces:
                # 创建另一个测试图像
                test_image2 = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
                faces2 = self.get_faces(test_image2)
                if faces2:
                    try:
                        self.face_swapper.get(test_image2, faces2[0], faces[0], paste_back=True)
                    except:
                        pass  # 预热失败不影响正常使用

            logger.info("模型预热完成")

        except Exception as e:
            logger.warning(f"模型预热失败: {e}")

    def clear_cache(self):
        """
        清理缓存和释放内存
        """
        try:
            import gc
            gc.collect()

            # 如果使用GPU，清理GPU缓存
            if 'CUDAExecutionProvider' in self.providers:
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        logger.info("GPU缓存已清理")
                except ImportError:
                    pass

            logger.info("内存缓存已清理")

        except Exception as e:
            logger.warning(f"缓存清理失败: {e}")

    def get_performance_info(self):
        """
        获取性能信息

        Returns:
            性能信息字典
        """
        info = {
            'providers': self.providers,
            'gpu_available': 'CUDAExecutionProvider' in self.providers or 'DmlExecutionProvider' in self.providers,
            'models_loaded': {
                'face_analyser': self.face_analyser is not None,
                'face_swapper': self.face_swapper is not None
            }
        }

        # 获取内存信息
        try:
            import psutil
            process = psutil.Process()
            info['memory_usage'] = {
                'rss': process.memory_info().rss / 1024 / 1024,  # MB
                'vms': process.memory_info().vms / 1024 / 1024   # MB
            }
        except ImportError:
            info['memory_usage'] = None

        # 获取GPU信息
        if info['gpu_available']:
            try:
                import torch
                if torch.cuda.is_available():
                    info['gpu_info'] = {
                        'device_count': torch.cuda.device_count(),
                        'current_device': torch.cuda.current_device(),
                        'memory_allocated': torch.cuda.memory_allocated() / 1024 / 1024,  # MB
                        'memory_reserved': torch.cuda.memory_reserved() / 1024 / 1024     # MB
                    }
            except ImportError:
                info['gpu_info'] = None

        return info

    def process_image(self, source_path: Union[str, Path], target_path: Union[str, Path],
                     output_path: Union[str, Path]) -> bool:
        """
        处理单张图像的换脸

        Args:
            source_path: 源人脸图像路径
            target_path: 目标图像路径
            output_path: 输出图像路径

        Returns:
            是否成功
        """
        try:
            logger.info(f"开始处理图像: {Path(source_path).name} → {Path(target_path).name}")

            # 读取图像
            source_image = cv2.imread(str(source_path))
            target_image = cv2.imread(str(target_path))

            if source_image is None:
                logger.error(f"无法读取源图像: {source_path}")
                return False

            if target_image is None:
                logger.error(f"无法读取目标图像: {target_path}")
                return False

            logger.info(f"源图像尺寸: {source_image.shape[:2]}")
            logger.info(f"目标图像尺寸: {target_image.shape[:2]}")

            # 检测源人脸
            logger.info("检测源图像中的人脸...")
            source_faces = self.get_faces(source_image)
            if not source_faces:
                logger.error("源图像中未检测到人脸")
                return False
            logger.info(f"源图像中检测到 {len(source_faces)} 个人脸")

            # 检测目标人脸
            logger.info("检测目标图像中的人脸...")
            target_faces = self.get_faces(target_image)
            if not target_faces:
                logger.error("目标图像中未检测到人脸")
                return False
            logger.info(f"目标图像中检测到 {len(target_faces)} 个人脸")

            # 执行换脸
            logger.info("开始执行换脸...")
            result_image = self.swap_face(source_image, target_image, source_faces[0], target_faces[0])

            if result_image is None:
                logger.error("换脸失败")
                return False

            # 保存结果
            logger.info(f"保存结果到: {output_path}")
            success = cv2.imwrite(str(output_path), result_image)

            if success:
                logger.info(f"✅ 图像换脸完成: {Path(output_path).name}")
                return True
            else:
                logger.error(f"保存图像失败: {output_path}")
                return False

        except Exception as e:
            logger.error(f"处理图像失败: {e}")
            return False
    
    def process_video(self, source_path: Union[str, Path], target_path: Union[str, Path],
                     output_path: Union[str, Path], progress_callback=None, stop_callback=None,
                     target_face_index=None, reference_face_path=None,
                     selected_face_indices=None, reference_frame_index=None) -> bool:
        """
        处理视频的换脸

        Args:
            source_path: 源人脸图像路径
            target_path: 目标视频路径
            output_path: 输出视频路径
            progress_callback: 进度回调函数
            stop_callback: 停止回调函数
            target_face_index: 目标人脸索引（旧版兼容）
            reference_face_path: 参考人脸路径
            selected_face_indices: 选中的人脸索引列表（新版多人脸选择）
            reference_frame_index: 参考帧索引（用于多人脸选择）

        Returns:
            是否成功
        """
        try:
            # 设置回调函数
            self.progress_callback = progress_callback
            self.stop_callback = stop_callback

            logger.info(f"开始处理视频: {Path(source_path).name} → {Path(target_path).name}")

            # 读取源人脸
            source_image = cv2.imread(str(source_path))
            if source_image is None:
                logger.error(f"无法读取源图像: {source_path}")
                return False

            # 检测源人脸
            logger.info("检测源图像中的人脸...")
            source_faces = self.get_faces(source_image)
            if not source_faces:
                logger.error("源图像中未检测到人脸")
                return False

            source_face = source_faces[0]
            logger.info(f"源图像中检测到 {len(source_faces)} 个人脸，使用第一个")
            
            # 打开视频
            cap = cv2.VideoCapture(str(target_path))
            if not cap.isOpened():
                logger.error(f"无法打开视频: {target_path}")
                return False
            
            # 获取视频信息
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            logger.info(f"视频属性信息: {width}x{height}, {fps}fps, {total_frames}帧")

            # 读取第一帧来获取实际尺寸
            ret, first_frame = cap.read()
            if ret:
                actual_height, actual_width = first_frame.shape[:2]
                logger.info(f"视频属性: {width}x{height}, 实际帧尺寸: {actual_width}x{actual_height}")

                # 使用实际帧尺寸创建VideoWriter
                width, height = actual_width, actual_height
                logger.info(f"使用实际帧尺寸: {width}x{height}")

                # 重置视频到开始
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            else:
                logger.error("无法读取视频第一帧")
                cap.release()
                return False

            duration = total_frames / fps if fps > 0 else 0
            logger.info(f"视频时长: {duration:.1f}秒")
            logger.info(f"输出路径: {output_path}")

            # 确保输出目录存在
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"输出目录: {output_file.parent.absolute()}")
            logger.info(f"完整输出路径: {output_file.absolute()}")



            # 创建视频写入器 - 使用MP4格式
            # 确保输出文件是.mp4格式
            if not str(output_path).endswith('.mp4'):
                output_path = str(output_path).rsplit('.', 1)[0] + '.mp4'

            # 使用mp4v编码器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

            if not out.isOpened():
                logger.error("无法创建视频写入器")
                cap.release()
                return False

            logger.info(f"视频写入器创建成功: {width}x{height} @ {fps}fps")
            logger.info(f"使用编码器: mp4v")
            logger.info(f"输出格式: MP4")

            # 创建一个测试文件来验证路径是否可写
            test_file = Path(output_path).with_suffix('.test')
            try:
                test_file.write_text("test")
                test_file.unlink()  # 删除测试文件
                logger.info("输出路径可写")
            except Exception as e:
                logger.error(f"输出路径不可写: {e}")
                cap.release()
                out.release()
                return False
            
            frame_count = 0
            reference_face_info = None  # 用于跟踪的参考人脸信息

            # 如果指定了参考人脸路径，从参考图像获取人脸信息
            if reference_face_path is not None:
                logger.info(f"使用人脸跟踪模式，参考人脸: {Path(reference_face_path).name}")

                # 读取参考人脸图像
                reference_image = cv2.imread(str(reference_face_path))
                if reference_image is not None:
                    # 检测参考图像中的人脸
                    reference_faces = self.get_faces_with_info(reference_image)
                    if reference_faces:
                        # 使用第一个检测到的人脸作为参考
                        reference_face_info = reference_faces[0]
                        logger.info(f"已设置参考人脸: 位置{reference_face_info['center']}, 大小{reference_face_info['area']}")
                    else:
                        logger.warning("参考图像中未检测到人脸，将使用自动模式")
                        reference_face_path = None
                else:
                    logger.error(f"无法读取参考人脸图像: {reference_face_path}")
                    reference_face_path = None

            # 如果指定了多个人脸索引（新版多人脸选择）
            elif selected_face_indices is not None and reference_frame_index is not None:
                logger.info(f"使用新版多人脸选择模式，参考帧: {reference_frame_index}, 人脸索引: {selected_face_indices}")

                # 跳转到参考帧
                cap.set(cv2.CAP_PROP_POS_FRAMES, reference_frame_index)
                ret, reference_frame = cap.read()
                if ret:
                    # 检测参考帧中的所有人脸
                    reference_frame_faces = self.get_faces_with_info(reference_frame)

                    # 获取选中的人脸信息
                    self.reference_faces_info = []
                    for face_idx in selected_face_indices:
                        if face_idx < len(reference_frame_faces):
                            face_info = reference_frame_faces[face_idx]
                            self.reference_faces_info.append(face_info)
                            logger.info(f"已设置参考人脸 {face_idx}: 位置{face_info['center']}, 大小{face_info['area']}")

                    if not self.reference_faces_info:
                        logger.warning("参考帧中没有找到选中的人脸，将使用自动模式")
                        selected_face_indices = None
                else:
                    logger.error(f"无法读取参考帧 {reference_frame_index}")
                    selected_face_indices = None

                # 重置视频到开始位置
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

            # 如果指定了目标人脸索引，需要从第一帧获取参考人脸信息（旧版兼容）
            elif target_face_index is not None:
                logger.info(f"使用旧版多人脸模式，目标人脸索引: {target_face_index}")

                # 读取第一帧
                ret, first_frame = cap.read()
                if ret:
                    # 检测第一帧中的所有人脸
                    first_frame_faces = self.get_faces_with_info(first_frame)
                    if first_frame_faces and target_face_index < len(first_frame_faces):
                        reference_face_info = first_frame_faces[target_face_index]
                        logger.info(f"已设置参考人脸: 索引{target_face_index}, 位置{reference_face_info['center']}, 大小{reference_face_info['area']}")
                    else:
                        logger.warning(f"第一帧中没有找到索引为{target_face_index}的人脸，将使用自动模式")
                        target_face_index = None

                # 重置视频到开始位置
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # 检查停止请求
                if stop_callback and stop_callback():
                    logger.info("收到停止请求，中断视频处理")
                    break

                # 检测当前帧中的人脸
                try:
                    target_faces = self.get_faces(frame)
                except Exception as e:
                    # 人脸检测失败，记录错误但继续处理
                    logger.error(f"帧 {frame_count}: 人脸检测失败: {e}")
                    target_faces = []

                if target_faces:
                    result_frame = frame.copy()

                    # 新版多人脸选择模式
                    if hasattr(self, 'reference_faces_info') and self.reference_faces_info:
                        # 对每个选中的参考人脸，找到匹配的目标人脸并进行替换
                        for ref_face_info in self.reference_faces_info:
                            matching_index = self.find_matching_face(target_faces, ref_face_info, frame_count=frame_count, total_frames=total_frames)
                            if matching_index is not None:
                                target_face_to_swap = target_faces[matching_index]
                                # 进行换脸
                                temp_result = self.swap_face(source_image, result_frame, source_face, target_face_to_swap)
                                if temp_result is not None:
                                    result_frame = temp_result

                        # 写入结果帧
                        out.write(result_frame)
                        # 发送预览更新
                        if hasattr(self, 'progress_callback') and self.progress_callback:
                            progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                            self.progress_callback(progress, frame_count, total_frames, None, frame, result_frame)

                    # 旧版单人脸模式
                    elif reference_face_info is not None:
                        # 多人脸模式：找到与参考人脸匹配的人脸
                        matching_index = self.find_matching_face(target_faces, reference_face_info, frame_count=frame_count, total_frames=total_frames)
                        if matching_index is not None:
                            target_face_to_swap = target_faces[matching_index]
                            # 进行换脸
                            result_frame = self.swap_face(source_image, frame, source_face, target_face_to_swap)
                            if result_frame is not None:
                                # 换脸成功，写入结果帧
                                out.write(result_frame)
                                # 每一帧都发送预览更新
                                if hasattr(self, 'progress_callback') and self.progress_callback:
                                    progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                                    self.progress_callback(progress, frame_count, total_frames, None, frame, result_frame)
                            else:
                                # 换脸失败，写入原帧
                                out.write(frame)
                                # 每一帧都发送预览更新
                                if hasattr(self, 'progress_callback') and self.progress_callback:
                                    progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                                    self.progress_callback(progress, frame_count, total_frames, None, frame, frame)
                        else:
                            # 没有找到匹配的人脸，写入原帧
                            out.write(frame)
                            if hasattr(self, 'progress_callback') and self.progress_callback:
                                progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                                self.progress_callback(progress, frame_count, total_frames, None, frame, frame)
                    else:
                        # 自动模式：使用第一个检测到的人脸
                        target_face_to_swap = target_faces[0]
                        result_frame = self.swap_face(source_image, frame, source_face, target_face_to_swap)
                        if result_frame is not None:
                            # 换脸成功，写入结果帧
                            out.write(result_frame)
                            # 每一帧都发送预览更新
                            if hasattr(self, 'progress_callback') and self.progress_callback:
                                progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                                self.progress_callback(progress, frame_count, total_frames, None, frame, result_frame)
                        else:
                            # 换脸失败，写入原帧
                            out.write(frame)
                            # 每一帧都发送预览更新
                            if hasattr(self, 'progress_callback') and self.progress_callback:
                                progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                                self.progress_callback(progress, frame_count, total_frames, None, frame, frame)
                else:
                    # 没有检测到人脸，直接写入原帧
                    out.write(frame)
                    # 每一帧都发送预览更新
                    if hasattr(self, 'progress_callback') and self.progress_callback:
                        progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                        self.progress_callback(progress, frame_count, total_frames, None, frame, frame)

                frame_count += 1

                # 进度回调
                if progress_callback:
                    progress = (frame_count / total_frames) * 100
                    try:
                        callback_result = progress_callback(progress, frame_count, total_frames)
                        # 如果回调返回False，也停止处理
                        if callback_result is False:
                            logger.info("进度回调请求停止处理")
                            break
                    except Exception as e:
                        logger.error(f"进度回调失败: {e}")

                # 每10帧记录一次日志并刷新写入器
                if frame_count % 10 == 0:
                    logger.info(f"已处理 {frame_count}/{total_frames} 帧")
                    # 刷新视频写入器缓冲区
                    try:
                        if hasattr(out, 'flush'):
                            out.flush()
                    except:
                        pass
            
            # 释放资源
            cap.release()
            if out is not None:
                logger.info("正在关闭视频写入器...")
                out.release()
                logger.info("视频写入器已关闭")

            # 强制刷新文件系统缓存
            import time
            time.sleep(2.0)  # 增加等待时间确保文件写入完成

            logger.info(f"检查输出文件: {output_path}")

            # 验证输出文件
            output_file = Path(output_path)
            logger.info(f"检查文件是否存在: {output_file.absolute()}")

            # 多次检查文件是否存在（有时需要等待文件系统同步）
            for i in range(5):
                if output_file.exists():
                    file_size = output_file.stat().st_size
                    if file_size > 0:
                        file_size_mb = file_size / (1024 * 1024)  # MB
                        logger.info(f"视频换脸完成: {output_path}")
                        logger.info(f"输出文件大小: {file_size_mb:.1f} MB")
                        logger.info(f"处理了 {frame_count} 帧")

                        # 保留音轨
                        self._preserve_audio(target_path, output_path)

                        return True
                    else:
                        logger.warning(f"输出文件为空，等待 {i+1}/5...")
                        time.sleep(0.5)
                else:
                    logger.warning(f"输出文件不存在，等待 {i+1}/5...")
                    time.sleep(0.5)

            # 最终检查失败
            logger.error(f"输出文件未生成或为空: {output_path}")
            logger.error(f"文件存在: {output_file.exists()}")
            if output_file.exists():
                logger.error(f"文件大小: {output_file.stat().st_size} 字节")

            # 列出输出目录的内容
            try:
                output_dir = output_file.parent
                logger.error(f"输出目录内容: {list(output_dir.iterdir())}")
            except:
                pass

            return False
            
        except Exception as e:
            logger.error(f"处理视频失败: {e}")
            return False

    def _preserve_audio(self, source_video_path: Union[str, Path], output_video_path: Union[str, Path]):
        """
        保留原视频的音轨

        Args:
            source_video_path: 原视频路径
            output_video_path: 输出视频路径
        """
        try:
            import subprocess

            # 检查FFmpeg是否可用，支持多种安装路径
            ffmpeg_cmd = self._find_ffmpeg()
            ffprobe_cmd = self._find_ffprobe()

            if not ffmpeg_cmd or not ffprobe_cmd:
                logger.warning("FFmpeg未找到，跳过音轨保留")
                logger.info("请确保FFmpeg已安装并在以下位置之一：")
                logger.info("1. 系统PATH中")
                logger.info("2. 当前目录下的ffmpeg文件夹")
                logger.info("3. C:/ffmpeg/bin/ (Windows)")
                logger.info("4. /usr/local/bin/ (Linux/Mac)")
                return

            # 检查原视频是否有音轨
            probe_cmd = [
                ffprobe_cmd,
                '-v', 'quiet',
                '-select_streams', 'a:0',
                '-show_entries', 'stream=codec_type',
                '-of', 'csv=p=0',
                str(source_video_path)
            ]

            try:
                probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
                if 'audio' not in probe_result.stdout:
                    logger.info("原视频没有音轨，跳过音轨保留")
                    return
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("无法检测音轨信息，尝试直接合并")

            # 创建临时文件名
            temp_output = str(output_video_path).replace('.mp4', '_temp.mp4')

            # 使用FFmpeg合并视频和音频
            cmd = [
                ffmpeg_cmd,
                '-i', str(output_video_path),  # 换脸后的视频
                '-i', str(source_video_path),  # 原视频（音频源）
                '-c:v', 'copy',  # 复制视频流
                '-c:a', 'aac',   # 音频编码
                '-map', '0:v:0', # 使用第一个文件的视频
                '-map', '1:a:0?', # 使用第二个文件的音频（可选）
                '-shortest',     # 以最短的流为准
                '-y',           # 覆盖输出文件
                temp_output
            ]

            logger.info("正在合并音轨...")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                # 替换原文件
                import shutil
                shutil.move(temp_output, output_video_path)
                logger.info("音轨合并完成")
            else:
                logger.warning(f"音轨合并失败: {result.stderr}")
                # 删除临时文件
                if Path(temp_output).exists():
                    Path(temp_output).unlink()

        except Exception as e:
            logger.warning(f"音轨保留失败: {e}")
            logger.info("提示: 如需音轨保留功能，请安装FFmpeg并确保在PATH中")
            # 即使音轨保留失败，也不影响主要功能

    def _find_ffmpeg(self):
        """查找FFmpeg可执行文件"""
        import platform
        import os

        # 可能的FFmpeg路径
        possible_paths = []

        if platform.system() == "Windows":
            # Windows常见路径 - 优先检查项目目录
            possible_paths = [
                "ffmpeg/ffmpeg.exe",  # 项目目录下的便携版
                "ffmpeg.exe",
                "ffmpeg/bin/ffmpeg.exe",
                "C:/ffmpeg/bin/ffmpeg.exe",
                "C:/Program Files/ffmpeg/bin/ffmpeg.exe",
                "C:/ProgramData/chocolatey/bin/ffmpeg.exe",  # Chocolatey安装路径
                os.path.expanduser("~/ffmpeg/bin/ffmpeg.exe")
            ]
        else:
            # Linux/Mac路径
            possible_paths = [
                "ffmpeg",
                "./ffmpeg",
                "/usr/local/bin/ffmpeg",
                "/usr/bin/ffmpeg",
                "/opt/homebrew/bin/ffmpeg",  # Mac M1
                os.path.expanduser("~/bin/ffmpeg")
            ]

        # 首先尝试PATH中的ffmpeg
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return 'ffmpeg'
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # 尝试其他路径
        for path in possible_paths:
            try:
                if os.path.exists(path):
                    subprocess.run([path, '-version'], capture_output=True, check=True)
                    return path
            except (subprocess.CalledProcessError, FileNotFoundError, OSError):
                continue

        return None

    def _find_ffprobe(self):
        """查找FFprobe可执行文件"""
        import platform
        import os

        # 可能的FFprobe路径
        possible_paths = []

        if platform.system() == "Windows":
            # Windows常见路径 - 优先检查项目目录
            possible_paths = [
                "ffmpeg/ffprobe.exe",  # 项目目录下的便携版
                "ffprobe.exe",
                "ffmpeg/bin/ffprobe.exe",
                "C:/ffmpeg/bin/ffprobe.exe",
                "C:/Program Files/ffmpeg/bin/ffprobe.exe",
                "C:/ProgramData/chocolatey/bin/ffprobe.exe",  # Chocolatey安装路径
                os.path.expanduser("~/ffmpeg/bin/ffprobe.exe")
            ]
        else:
            # Linux/Mac路径
            possible_paths = [
                "ffprobe",
                "./ffprobe",
                "/usr/local/bin/ffprobe",
                "/usr/bin/ffprobe",
                "/opt/homebrew/bin/ffprobe",  # Mac M1
                os.path.expanduser("~/bin/ffprobe")
            ]

        # 首先尝试PATH中的ffprobe
        try:
            subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
            return 'ffprobe'
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # 尝试其他路径
        for path in possible_paths:
            try:
                if os.path.exists(path):
                    subprocess.run([path, '-version'], capture_output=True, check=True)
                    return path
            except (subprocess.CalledProcessError, FileNotFoundError, OSError):
                continue

        return None
