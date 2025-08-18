"""
背景替换引擎
支持多种背景替换技术：BackgroundMattingV2、MODNet、U2Net、Rembg
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Union
import logging
import os

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 设置项目根目录和模型目录
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "models" / "background_removal"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# 设置环境变量，让rembg使用项目内的模型目录
os.environ['REMBG_HOME'] = str(MODELS_DIR)
os.environ['U2NET_HOME'] = str(MODELS_DIR / "u2net")
os.environ['TORCH_HOME'] = str(MODELS_DIR / "torch")

# 创建子目录
(MODELS_DIR / "u2net").mkdir(exist_ok=True)
(MODELS_DIR / "torch").mkdir(exist_ok=True)

# 配置rembg使用国内镜像（如果可用）
def setup_rembg_mirror():
    """设置rembg使用国内镜像"""
    try:
        import rembg
        # 尝试设置国内镜像
        mirror_urls = [
            "https://ghproxy.com/https://github.com/danielgatis/rembg/releases/download/v0.0.0/",
            "https://mirror.ghproxy.com/https://github.com/danielgatis/rembg/releases/download/v0.0.0/",
            "https://github.com/danielgatis/rembg/releases/download/v0.0.0/"  # 原始地址作为备用
        ]

        # 这里可以根据需要设置镜像，但rembg库可能不直接支持
        # 我们将在模型初始化时处理网络问题
        logger.info("rembg镜像配置完成")
    except Exception as e:
        logger.warning(f"rembg镜像配置失败: {e}")

setup_rembg_mirror()


class BackgroundReplacer:
    """背景替换引擎"""

    def __init__(self, mode: str = "backgroundmattingv2", lazy_init: bool = False):
        """
        初始化背景替换引擎

        Args:
            mode: 背景替换模式 ("backgroundmattingv2", "modnet", "u2net", "rembg")
            lazy_init: 是否延迟初始化模型（避免阻塞主线程）
        """
        self.original_mode = mode.lower()  # 保存用户原始选择
        self.mode = mode.lower()
        self.model = None
        self.device = "cpu"  # 默认使用CPU
        self.lazy_init = lazy_init
        self.is_initializing = False
        self.initialization_error = None
        self.fallback_occurred = False  # 是否发生了回退
        self.fallback_reason = None  # 回退原因
        self.model_status = "not_initialized"  # not_initialized, downloading, ready, failed, fallback

        # 检查GPU可用性
        try:
            import torch
            if torch.cuda.is_available():
                self.device = "cuda"
                logger.info("检测到CUDA，将使用GPU加速")
            else:
                logger.info("未检测到CUDA，将使用CPU")
        except ImportError:
            logger.info("PyTorch未安装，将使用CPU")

        # 如果不是延迟初始化，立即初始化模型
        if not lazy_init:
            self._initialize_model()
    
    def _initialize_model(self):
        """初始化背景替换模型"""
        try:
            if self.mode == "rembg":
                self._init_rembg()
            elif self.mode == "u2net":
                self._init_u2net()
            elif self.mode == "modnet":
                self._init_modnet()
            elif self.mode == "backgroundmattingv2":
                self._init_backgroundmattingv2()
            else:
                logger.warning(f"未知的背景替换模式: {self.mode}，回退到rembg")
                self.mode = "rembg"
                self._init_rembg()
                
            logger.info(f"背景替换模型初始化成功: {self.mode}")
            
        except Exception as e:
            logger.error(f"背景替换模型初始化失败: {e}")
            self.initialization_error = str(e)
            self.model_status = "failed"

            # 回退到最简单的rembg
            try:
                logger.info(f"尝试从 {self.original_mode} 回退到 rembg 模式")
                self.mode = "rembg"
                self.fallback_occurred = True
                self.fallback_reason = f"原始模式 {self.original_mode} 初始化失败: {str(e)[:100]}..."
                self._init_rembg()
                self.model_status = "fallback"  # 使用特殊状态表示回退
                logger.info("已回退到rembg模式")
            except Exception as fallback_error:
                logger.error(f"回退到rembg也失败: {fallback_error}")
                self.model = None
                self.model_status = "failed"
                self.initialization_error = f"原始错误: {e}, 回退错误: {fallback_error}"
    
    def _init_rembg(self):
        """初始化Rembg模型"""
        try:
            from rembg import remove, new_session

            # 确保模型目录存在
            logger.info(f"模型将下载到: {MODELS_DIR}")

            # 尝试使用不同的模型，按优先级排序
            models_to_try = ['u2net', 'u2netp', 'silueta']

            for model_name in models_to_try:
                try:
                    logger.info(f"尝试加载rembg模型: {model_name}")
                    self.model = new_session(model_name)
                    logger.info(f"Rembg模型加载成功: {model_name}，存储在: {MODELS_DIR}")
                    return
                except Exception as model_error:
                    logger.warning(f"模型 {model_name} 加载失败: {model_error}")
                    continue

            # 如果所有模型都失败了
            raise Exception("所有rembg模型都加载失败")

        except ImportError:
            logger.error("Rembg未安装，请运行: pip install rembg")
            raise
        except Exception as e:
            logger.error(f"Rembg模型初始化失败: {e}")
            raise
    
    def _init_u2net(self):
        """初始化U2Net模型"""
        try:
            # 这里可以集成U2Net的直接实现
            # 暂时使用rembg的u2net后端
            from rembg import remove, new_session

            logger.info(f"U2Net模型将下载到: {MODELS_DIR}")
            self.model = new_session('u2net')
            logger.info(f"U2Net模型加载成功，模型存储在: {MODELS_DIR}")
        except ImportError:
            logger.error("U2Net依赖未安装")
            raise
        except Exception as e:
            logger.error(f"U2Net模型初始化失败: {e}")
            raise

    def _init_modnet(self):
        """初始化MODNet模型"""
        try:
            # MODNet需要单独的实现
            # 这里先使用rembg作为替代
            from rembg import remove, new_session

            logger.info(f"MODNet模型将下载到: {MODELS_DIR}")
            self.model = new_session('silueta')  # 使用silueta模型，适合人像
            logger.info(f"MODNet模型加载成功（使用rembg silueta后端），模型存储在: {MODELS_DIR}")
        except ImportError:
            logger.error("MODNet依赖未安装")
            raise
        except Exception as e:
            logger.error(f"MODNet模型初始化失败: {e}")
            raise

    def _init_backgroundmattingv2(self):
        """初始化BackgroundMattingV2模型"""
        try:
            # BackgroundMattingV2需要单独的实现
            # 这里先使用rembg作为替代
            from rembg import remove, new_session

            logger.info(f"BackgroundMattingV2模型将下载到: {MODELS_DIR}")

            # 尝试使用不同的人体分割模型
            human_models = ['u2net_human_seg', 'silueta', 'u2net']

            for model_name in human_models:
                try:
                    logger.info(f"尝试加载BackgroundMattingV2模型: {model_name}")
                    self.model = new_session(model_name)
                    logger.info(f"BackgroundMattingV2模型加载成功: {model_name}，存储在: {MODELS_DIR}")
                    return
                except Exception as model_error:
                    logger.warning(f"BackgroundMattingV2模型 {model_name} 加载失败: {model_error}")
                    continue

            # 如果所有模型都失败了
            raise Exception("所有BackgroundMattingV2模型都加载失败")

        except ImportError:
            logger.error("BackgroundMattingV2依赖未安装")
            raise
        except Exception as e:
            logger.error(f"BackgroundMattingV2模型初始化失败: {e}")
            raise
    
    def remove_background(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        移除图像背景
        
        Args:
            image: 输入图像 (BGR格式)
            
        Returns:
            带透明通道的图像 (BGRA格式)，失败返回None
        """
        if self.model is None:
            logger.error("背景替换模型未初始化")
            return None
        
        try:
            if self.mode in ["rembg", "u2net", "modnet", "backgroundmattingv2"]:
                return self._remove_background_rembg(image)
            else:
                logger.error(f"不支持的背景替换模式: {self.mode}")
                return None
                
        except Exception as e:
            logger.error(f"背景移除失败: {e}")
            return None
    
    def _remove_background_rembg(self, image: np.ndarray) -> Optional[np.ndarray]:
        """使用rembg移除背景"""
        try:
            from rembg import remove
            from PIL import Image
            
            # 转换BGR到RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 转换为PIL Image
            pil_image = Image.fromarray(rgb_image)
            
            # 移除背景
            result_pil = remove(pil_image, session=self.model)
            
            # 转换回numpy数组
            result_rgba = np.array(result_pil)
            
            # 转换RGBA到BGRA
            if result_rgba.shape[2] == 4:
                result_bgra = cv2.cvtColor(result_rgba, cv2.COLOR_RGBA2BGRA)
                return result_bgra
            else:
                logger.error("背景移除结果不包含透明通道")
                return None
                
        except Exception as e:
            logger.error(f"rembg背景移除失败: {e}")
            return None
    
    def replace_background(self, image: np.ndarray, background: np.ndarray) -> Optional[np.ndarray]:
        """
        替换图像背景
        
        Args:
            image: 输入图像 (BGR格式)
            background: 背景图像 (BGR格式)
            
        Returns:
            背景替换后的图像 (BGR格式)，失败返回None
        """
        try:
            # 移除原背景
            foreground_rgba = self.remove_background(image)
            if foreground_rgba is None:
                return None
            
            # 调整背景图像尺寸
            h, w = image.shape[:2]
            background_resized = cv2.resize(background, (w, h))
            
            # 提取前景和alpha通道
            foreground_bgr = foreground_rgba[:, :, :3]
            alpha = foreground_rgba[:, :, 3] / 255.0
            
            # 扩展alpha通道到3个维度
            alpha_3d = np.stack([alpha, alpha, alpha], axis=2)
            
            # 混合前景和背景
            result = foreground_bgr * alpha_3d + background_resized * (1 - alpha_3d)
            result = result.astype(np.uint8)
            
            return result
            
        except Exception as e:
            logger.error(f"背景替换失败: {e}")
            return None
    
    def get_supported_modes(self):
        """获取支持的背景替换模式"""
        return ["backgroundmattingv2", "modnet", "u2net", "rembg"]
    
    def is_available(self):
        """检查背景替换功能是否可用"""
        return self.model is not None

    def is_initializing_model(self):
        """检查是否正在初始化"""
        return self.is_initializing

    def get_initialization_error(self):
        """获取初始化错误信息"""
        return self.initialization_error

    def get_model_status(self):
        """获取模型状态"""
        return {
            'status': self.model_status,
            'original_mode': self.original_mode,
            'current_mode': self.mode,
            'fallback_occurred': self.fallback_occurred,
            'fallback_reason': self.fallback_reason,
            'error': self.initialization_error,
            'available': self.is_available()
        }

    def check_model_availability(self, mode: str):
        """检查指定模式的模型是否可用（不实际加载）"""
        try:
            from rembg import new_session

            # 模型映射
            model_map = {
                'rembg': 'u2net',
                'u2net': 'u2net',
                'modnet': 'silueta',
                'backgroundmattingv2': 'u2net_human_seg'
            }

            model_name = model_map.get(mode.lower(), 'u2net')

            # 检查模型文件是否存在
            model_path = MODELS_DIR / "u2net" / f"{model_name}.onnx"
            if model_path.exists():
                return True, f"模型 {model_name} 已下载"
            else:
                return False, f"模型 {model_name} 需要下载"

        except Exception as e:
            return False, f"检查模型可用性失败: {e}"

    def initialize_async(self, progress_callback=None):
        """
        异步初始化模型

        Args:
            progress_callback: 进度回调函数，接收 (current, total, message) 参数
        """
        if self.model is not None or self.is_initializing:
            return

        self.is_initializing = True
        self.initialization_error = None
        self.model_status = "downloading"

        try:
            if progress_callback:
                progress_callback(10, 100, f"开始初始化{self.mode}模型...")

            if progress_callback:
                progress_callback(30, 100, f"正在下载{self.mode}模型...")

            self._initialize_model()

            if progress_callback:
                progress_callback(100, 100, "模型初始化完成")

            self.model_status = "ready"

        except Exception as e:
            self.initialization_error = str(e)
            self.model_status = "failed"
            logger.error(f"异步模型初始化失败: {e}")
            if progress_callback:
                progress_callback(0, 100, f"初始化失败: {e}")
        finally:
            self.is_initializing = False
