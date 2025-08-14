"""
颜色处理工具模块

提供颜色匹配、色彩校正、色彩空间转换等功能。
"""

import cv2
import numpy as np
from typing import Tuple, Optional
from ..utils.logger import LoggerMixin

class ColorUtils(LoggerMixin):
    """颜色处理工具类"""
    
    @staticmethod
    def match_histogram(source: np.ndarray, reference: np.ndarray, 
                       mask: Optional[np.ndarray] = None) -> np.ndarray:
        """
        直方图匹配 - 将源图像的颜色分布匹配到参考图像
        
        Args:
            source: 源图像
            reference: 参考图像
            mask: 可选的掩码，指定匹配区域
            
        Returns:
            np.ndarray: 匹配后的图像
        """
        if len(source.shape) != len(reference.shape):
            raise ValueError("源图像和参考图像的维度必须相同")
        
        if len(source.shape) == 2:
            # 灰度图像
            return ColorUtils._match_histogram_single_channel(source, reference, mask)
        else:
            # 彩色图像，分别处理每个通道
            result = np.zeros_like(source)
            for i in range(source.shape[2]):
                src_channel = source[:, :, i]
                ref_channel = reference[:, :, i]
                channel_mask = mask if mask is None else mask
                result[:, :, i] = ColorUtils._match_histogram_single_channel(
                    src_channel, ref_channel, channel_mask
                )
            return result
    
    @staticmethod
    def _match_histogram_single_channel(source: np.ndarray, reference: np.ndarray,
                                      mask: Optional[np.ndarray] = None) -> np.ndarray:
        """单通道直方图匹配"""
        # 计算直方图
        if mask is not None:
            src_hist = cv2.calcHist([source], [0], mask, [256], [0, 256])
            ref_hist = cv2.calcHist([reference], [0], mask, [256], [0, 256])
        else:
            src_hist = cv2.calcHist([source], [0], None, [256], [0, 256])
            ref_hist = cv2.calcHist([reference], [0], None, [256], [0, 256])
        
        # 计算累积分布函数
        src_cdf = np.cumsum(src_hist).astype(np.float64)
        ref_cdf = np.cumsum(ref_hist).astype(np.float64)
        
        # 归一化
        src_cdf /= src_cdf[-1]
        ref_cdf /= ref_cdf[-1]
        
        # 创建查找表
        lut = np.zeros(256, dtype=np.uint8)
        for i in range(256):
            # 找到最接近的参考值
            diff = np.abs(ref_cdf - src_cdf[i])
            lut[i] = np.argmin(diff)
        
        # 应用查找表
        return cv2.LUT(source, lut)
    
    @staticmethod
    def color_transfer(source: np.ndarray, reference: np.ndarray,
                      mask: Optional[np.ndarray] = None) -> np.ndarray:
        """
        颜色传输 - 使用LAB色彩空间的均值和标准差匹配
        
        Args:
            source: 源图像
            reference: 参考图像
            mask: 可选的掩码
            
        Returns:
            np.ndarray: 颜色传输后的图像
        """
        # 转换到LAB色彩空间
        source_lab = cv2.cvtColor(source, cv2.COLOR_BGR2LAB).astype(np.float32)
        reference_lab = cv2.cvtColor(reference, cv2.COLOR_BGR2LAB).astype(np.float32)
        
        # 计算统计信息
        if mask is not None:
            mask_bool = mask > 0
            src_mean = np.array([np.mean(source_lab[:, :, i][mask_bool]) for i in range(3)])
            src_std = np.array([np.std(source_lab[:, :, i][mask_bool]) for i in range(3)])
            ref_mean = np.array([np.mean(reference_lab[:, :, i][mask_bool]) for i in range(3)])
            ref_std = np.array([np.std(reference_lab[:, :, i][mask_bool]) for i in range(3)])
        else:
            src_mean = np.mean(source_lab.reshape(-1, 3), axis=0)
            src_std = np.std(source_lab.reshape(-1, 3), axis=0)
            ref_mean = np.mean(reference_lab.reshape(-1, 3), axis=0)
            ref_std = np.std(reference_lab.reshape(-1, 3), axis=0)
        
        # 避免除零
        src_std = np.where(src_std == 0, 1, src_std)
        
        # 应用颜色传输
        result_lab = source_lab.copy()
        for i in range(3):
            result_lab[:, :, i] = (source_lab[:, :, i] - src_mean[i]) * (ref_std[i] / src_std[i]) + ref_mean[i]
        
        # 限制到有效范围
        result_lab = np.clip(result_lab, 0, 255)
        
        # 转换回BGR
        return cv2.cvtColor(result_lab.astype(np.uint8), cv2.COLOR_LAB2BGR)
    
    @staticmethod
    def white_balance(image: np.ndarray, method: str = 'gray_world') -> np.ndarray:
        """
        白平衡校正
        
        Args:
            image: 输入图像
            method: 白平衡方法 ('gray_world', 'white_patch')
            
        Returns:
            np.ndarray: 白平衡后的图像
        """
        if method == 'gray_world':
            return ColorUtils._gray_world_white_balance(image)
        elif method == 'white_patch':
            return ColorUtils._white_patch_white_balance(image)
        else:
            raise ValueError(f"未知的白平衡方法: {method}")
    
    @staticmethod
    def _gray_world_white_balance(image: np.ndarray) -> np.ndarray:
        """灰度世界白平衡"""
        # 计算每个通道的平均值
        mean_b = np.mean(image[:, :, 0])
        mean_g = np.mean(image[:, :, 1])
        mean_r = np.mean(image[:, :, 2])
        
        # 计算整体平均值
        gray_mean = (mean_b + mean_g + mean_r) / 3
        
        # 计算缩放因子
        scale_b = gray_mean / mean_b if mean_b > 0 else 1
        scale_g = gray_mean / mean_g if mean_g > 0 else 1
        scale_r = gray_mean / mean_r if mean_r > 0 else 1
        
        # 应用缩放
        result = image.astype(np.float32)
        result[:, :, 0] *= scale_b
        result[:, :, 1] *= scale_g
        result[:, :, 2] *= scale_r
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    @staticmethod
    def _white_patch_white_balance(image: np.ndarray) -> np.ndarray:
        """白斑白平衡"""
        # 找到每个通道的最大值
        max_b = np.max(image[:, :, 0])
        max_g = np.max(image[:, :, 1])
        max_r = np.max(image[:, :, 2])
        
        # 计算缩放因子
        scale_b = 255.0 / max_b if max_b > 0 else 1
        scale_g = 255.0 / max_g if max_g > 0 else 1
        scale_r = 255.0 / max_r if max_r > 0 else 1
        
        # 应用缩放
        result = image.astype(np.float32)
        result[:, :, 0] *= scale_b
        result[:, :, 1] *= scale_g
        result[:, :, 2] *= scale_r
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    @staticmethod
    def adjust_color_temperature(image: np.ndarray, temperature: float) -> np.ndarray:
        """
        调整色温
        
        Args:
            image: 输入图像
            temperature: 色温调整值 (-100 到 100)
            
        Returns:
            np.ndarray: 调整后的图像
        """
        # 转换到浮点数
        img_float = image.astype(np.float32)
        
        # 色温调整矩阵
        if temperature > 0:
            # 暖色调
            factor = temperature / 100.0
            img_float[:, :, 0] *= (1 - factor * 0.2)  # 减少蓝色
            img_float[:, :, 2] *= (1 + factor * 0.1)  # 增加红色
        else:
            # 冷色调
            factor = -temperature / 100.0
            img_float[:, :, 0] *= (1 + factor * 0.2)  # 增加蓝色
            img_float[:, :, 2] *= (1 - factor * 0.1)  # 减少红色
        
        return np.clip(img_float, 0, 255).astype(np.uint8)
    
    @staticmethod
    def enhance_saturation(image: np.ndarray, saturation: float) -> np.ndarray:
        """
        调整饱和度
        
        Args:
            image: 输入图像
            saturation: 饱和度调整 (0.0 到 2.0，1.0为原始)
            
        Returns:
            np.ndarray: 调整后的图像
        """
        # 转换到HSV色彩空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # 调整饱和度通道
        hsv[:, :, 1] *= saturation
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        
        # 转换回BGR
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    @staticmethod
    def gamma_correction(image: np.ndarray, gamma: float) -> np.ndarray:
        """
        伽马校正
        
        Args:
            image: 输入图像
            gamma: 伽马值 (0.1 到 3.0)
            
        Returns:
            np.ndarray: 校正后的图像
        """
        # 创建查找表
        inv_gamma = 1.0 / gamma
        lut = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype(np.uint8)
        
        # 应用查找表
        return cv2.LUT(image, lut)
    
    @staticmethod
    def blend_colors(color1: np.ndarray, color2: np.ndarray, 
                    alpha: float, mode: str = 'normal') -> np.ndarray:
        """
        颜色混合
        
        Args:
            color1: 第一个颜色图像
            color2: 第二个颜色图像
            alpha: 混合比例 (0.0 到 1.0)
            mode: 混合模式 ('normal', 'multiply', 'screen', 'overlay')
            
        Returns:
            np.ndarray: 混合后的图像
        """
        if mode == 'normal':
            return cv2.addWeighted(color1, 1 - alpha, color2, alpha, 0)
        
        # 转换到浮点数进行计算
        c1 = color1.astype(np.float32) / 255.0
        c2 = color2.astype(np.float32) / 255.0
        
        if mode == 'multiply':
            blended = c1 * c2
        elif mode == 'screen':
            blended = 1 - (1 - c1) * (1 - c2)
        elif mode == 'overlay':
            blended = np.where(c1 < 0.5, 2 * c1 * c2, 1 - 2 * (1 - c1) * (1 - c2))
        else:
            blended = c2  # 默认为normal
        
        # 应用alpha混合
        result = c1 * (1 - alpha) + blended * alpha
        
        return (np.clip(result, 0, 1) * 255).astype(np.uint8)
