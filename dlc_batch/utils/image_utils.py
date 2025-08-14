"""
图像处理工具模块

提供图像处理、变换、增强等功能。
"""

import cv2
import numpy as np
from typing import Tuple, Optional, List, Union
from ..utils.logger import LoggerMixin

class ImageUtils(LoggerMixin):
    """图像处理工具类"""
    
    @staticmethod
    def resize_image(image: np.ndarray, target_size: Tuple[int, int], 
                    keep_aspect_ratio: bool = True, 
                    interpolation: int = cv2.INTER_LINEAR) -> np.ndarray:
        """
        调整图像尺寸
        
        Args:
            image: 输入图像
            target_size: 目标尺寸 (width, height)
            keep_aspect_ratio: 是否保持宽高比
            interpolation: 插值方法
            
        Returns:
            np.ndarray: 调整后的图像
        """
        if not keep_aspect_ratio:
            return cv2.resize(image, target_size, interpolation=interpolation)
        
        h, w = image.shape[:2]
        target_w, target_h = target_size
        
        # 计算缩放比例
        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # 调整尺寸
        resized = cv2.resize(image, (new_w, new_h), interpolation=interpolation)
        
        # 如果需要，添加填充
        if new_w != target_w or new_h != target_h:
            # 创建目标尺寸的黑色图像
            result = np.zeros((target_h, target_w, image.shape[2]), dtype=image.dtype)
            
            # 计算居中位置
            y_offset = (target_h - new_h) // 2
            x_offset = (target_w - new_w) // 2
            
            # 将调整后的图像放置在中心
            result[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
            return result
        
        return resized
    
    @staticmethod
    def crop_image(image: np.ndarray, bbox: Tuple[int, int, int, int], 
                  expand_ratio: float = 0.0) -> np.ndarray:
        """
        裁剪图像
        
        Args:
            image: 输入图像
            bbox: 边界框 (x, y, width, height)
            expand_ratio: 扩展比例
            
        Returns:
            np.ndarray: 裁剪后的图像
        """
        h, w = image.shape[:2]
        x, y, box_w, box_h = bbox
        
        if expand_ratio > 0:
            # 扩展边界框
            expand_w = int(box_w * expand_ratio)
            expand_h = int(box_h * expand_ratio)
            
            x = max(0, x - expand_w // 2)
            y = max(0, y - expand_h // 2)
            box_w = min(w - x, box_w + expand_w)
            box_h = min(h - y, box_h + expand_h)
        
        # 确保边界框在图像范围内
        x = max(0, min(x, w - 1))
        y = max(0, min(y, h - 1))
        x2 = min(w, x + box_w)
        y2 = min(h, y + box_h)
        
        return image[y:y2, x:x2]
    
    @staticmethod
    def paste_image(background: np.ndarray, foreground: np.ndarray, 
                   position: Tuple[int, int], mask: Optional[np.ndarray] = None,
                   blend_mode: str = 'normal') -> np.ndarray:
        """
        将前景图像粘贴到背景图像上
        
        Args:
            background: 背景图像
            foreground: 前景图像
            position: 粘贴位置 (x, y)
            mask: 可选的掩码
            blend_mode: 混合模式 ('normal', 'multiply', 'overlay')
            
        Returns:
            np.ndarray: 合成后的图像
        """
        result = background.copy()
        x, y = position
        h, w = foreground.shape[:2]
        bg_h, bg_w = background.shape[:2]
        
        # 计算有效区域
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(bg_w, x + w)
        y2 = min(bg_h, y + h)
        
        if x2 <= x1 or y2 <= y1:
            return result  # 没有重叠区域
        
        # 计算前景图像的对应区域
        fg_x1 = x1 - x
        fg_y1 = y1 - y
        fg_x2 = fg_x1 + (x2 - x1)
        fg_y2 = fg_y1 + (y2 - y1)
        
        fg_region = foreground[fg_y1:fg_y2, fg_x1:fg_x2]
        bg_region = result[y1:y2, x1:x2]
        
        if mask is not None:
            mask_region = mask[fg_y1:fg_y2, fg_x1:fg_x2]
            if len(mask_region.shape) == 2:
                mask_region = mask_region[:, :, np.newaxis]
            mask_region = mask_region.astype(np.float32) / 255.0
        else:
            mask_region = np.ones_like(fg_region[:, :, :1], dtype=np.float32)
        
        # 应用混合模式
        if blend_mode == 'normal':
            blended = fg_region
        elif blend_mode == 'multiply':
            blended = (fg_region.astype(np.float32) * bg_region.astype(np.float32) / 255.0).astype(np.uint8)
        elif blend_mode == 'overlay':
            # 简化的overlay模式
            blended = cv2.addWeighted(bg_region, 0.5, fg_region, 0.5, 0)
        else:
            blended = fg_region
        
        # 应用掩码
        result[y1:y2, x1:x2] = (blended * mask_region + bg_region * (1 - mask_region)).astype(np.uint8)
        
        return result
    
    @staticmethod
    def create_gaussian_mask(size: Tuple[int, int], center: Tuple[int, int], 
                           sigma: float) -> np.ndarray:
        """
        创建高斯掩码
        
        Args:
            size: 掩码尺寸 (width, height)
            center: 中心点 (x, y)
            sigma: 高斯标准差
            
        Returns:
            np.ndarray: 高斯掩码
        """
        w, h = size
        cx, cy = center
        
        y, x = np.ogrid[:h, :w]
        mask = np.exp(-((x - cx)**2 + (y - cy)**2) / (2 * sigma**2))
        
        return (mask * 255).astype(np.uint8)
    
    @staticmethod
    def apply_gaussian_blur(image: np.ndarray, kernel_size: int = 5, 
                          sigma: float = 0) -> np.ndarray:
        """
        应用高斯模糊
        
        Args:
            image: 输入图像
            kernel_size: 核大小 (必须为奇数)
            sigma: 高斯标准差，0表示自动计算
            
        Returns:
            np.ndarray: 模糊后的图像
        """
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma)
    
    @staticmethod
    def adjust_brightness_contrast(image: np.ndarray, brightness: float = 0, 
                                 contrast: float = 1.0) -> np.ndarray:
        """
        调整图像亮度和对比度
        
        Args:
            image: 输入图像
            brightness: 亮度调整 (-100 到 100)
            contrast: 对比度调整 (0.5 到 3.0)
            
        Returns:
            np.ndarray: 调整后的图像
        """
        # 转换为浮点数进行计算
        img_float = image.astype(np.float32)
        
        # 应用对比度和亮度调整
        adjusted = img_float * contrast + brightness
        
        # 限制到有效范围并转换回uint8
        adjusted = np.clip(adjusted, 0, 255)
        return adjusted.astype(np.uint8)
    
    @staticmethod
    def histogram_equalization(image: np.ndarray, clip_limit: float = 2.0) -> np.ndarray:
        """
        直方图均衡化
        
        Args:
            image: 输入图像
            clip_limit: CLAHE的裁剪限制
            
        Returns:
            np.ndarray: 均衡化后的图像
        """
        if len(image.shape) == 3:
            # 彩色图像，转换到LAB空间处理L通道
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            # 灰度图像
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            return clahe.apply(image)
    
    @staticmethod
    def get_image_stats(image: np.ndarray) -> dict:
        """
        获取图像统计信息
        
        Args:
            image: 输入图像
            
        Returns:
            dict: 统计信息
        """
        stats = {
            'shape': image.shape,
            'dtype': str(image.dtype),
            'min': float(np.min(image)),
            'max': float(np.max(image)),
            'mean': float(np.mean(image)),
            'std': float(np.std(image))
        }
        
        if len(image.shape) == 3:
            stats['channels'] = image.shape[2]
            for i in range(image.shape[2]):
                channel = image[:, :, i]
                stats[f'channel_{i}'] = {
                    'min': float(np.min(channel)),
                    'max': float(np.max(channel)),
                    'mean': float(np.mean(channel)),
                    'std': float(np.std(channel))
                }
        
        return stats
