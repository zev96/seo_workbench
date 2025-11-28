"""
图片处理器
处理图片的尺寸调整、格式转换和 Alt 文本提取
"""

from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
from loguru import logger


class ImageProcessor:
    """图片处理器"""
    
    # 默认最大宽度（像素）
    DEFAULT_MAX_WIDTH = 600
    
    @staticmethod
    def get_image_alt_text(image_path: str) -> str:
        """
        从图片文件名提取 Alt 文本
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            Alt 文本（不含扩展名）
        """
        return Path(image_path).stem
    
    @staticmethod
    def resize_image(
        image_path: str,
        max_width: int = DEFAULT_MAX_WIDTH,
        max_height: Optional[int] = None,
        keep_aspect_ratio: bool = True
    ) -> Optional[Image.Image]:
        """
        调整图片尺寸
        
        Args:
            image_path: 图片文件路径
            max_width: 最大宽度
            max_height: 最大高度（可选）
            keep_aspect_ratio: 是否保持宽高比
            
        Returns:
            PIL Image 对象，失败返回 None
        """
        try:
            img = Image.open(image_path)
            original_width, original_height = img.size
            
            # 如果图片小于最大尺寸，不调整
            if original_width <= max_width and (max_height is None or original_height <= max_height):
                return img
            
            if keep_aspect_ratio:
                # 保持宽高比
                if max_height is None:
                    # 只限制宽度
                    ratio = max_width / original_width
                    new_width = max_width
                    new_height = int(original_height * ratio)
                else:
                    # 同时限制宽度和高度
                    width_ratio = max_width / original_width
                    height_ratio = max_height / original_height
                    ratio = min(width_ratio, height_ratio)
                    new_width = int(original_width * ratio)
                    new_height = int(original_height * ratio)
            else:
                # 不保持宽高比
                new_width = max_width
                new_height = max_height if max_height else original_height
            
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.debug(f"图片调整: {original_width}x{original_height} -> {new_width}x{new_height}")
            return resized_img
            
        except Exception as e:
            logger.error(f"调整图片尺寸失败: {e}")
            return None
    
    @staticmethod
    def get_image_size(image_path: str) -> Optional[Tuple[int, int]]:
        """
        获取图片尺寸
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            (宽度, 高度) 元组，失败返回 None
        """
        try:
            with Image.open(image_path) as img:
                return img.size
        except Exception as e:
            logger.error(f"获取图片尺寸失败: {e}")
            return None
    
    @staticmethod
    def convert_to_rgb(image_path: str) -> Optional[Image.Image]:
        """
        将图片转换为 RGB 模式（用于处理 PNG 透明背景等）
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            PIL Image 对象，失败返回 None
        """
        try:
            img = Image.open(image_path)
            if img.mode != 'RGB':
                # 创建白色背景
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                # 如果有透明通道，合成到白色背景上
                if img.mode == 'RGBA':
                    rgb_img.paste(img, mask=img.split()[3])
                else:
                    rgb_img.paste(img)
                logger.debug(f"图片转换: {img.mode} -> RGB")
                return rgb_img
            return img
        except Exception as e:
            logger.error(f"转换图片模式失败: {e}")
            return None
    
    @staticmethod
    def validate_image(image_path: str) -> bool:
        """
        验证图片文件是否有效
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            是否有效
        """
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception as e:
            logger.warning(f"图片文件无效: {image_path}, {e}")
            return False
    
    @staticmethod
    def get_cyclic_image(image_list: list, index: int) -> Optional[str]:
        """
        循环获取图片（图片不足时自动重复）
        
        Args:
            image_list: 图片路径列表
            index: 索引
            
        Returns:
            图片路径，列表为空返回 None
        """
        if not image_list:
            logger.warning("图片列表为空")
            return None
        
        # 使用取模实现循环
        cyclic_index = index % len(image_list)
        return str(image_list[cyclic_index])
    
    @staticmethod
    def calculate_word_image_size(
        original_width: int,
        original_height: int,
        max_width_inches: float = 6.0
    ) -> Tuple[int, int]:
        """
        计算插入 Word 文档的图片尺寸（英寸）
        
        Args:
            original_width: 原始宽度（像素）
            original_height: 原始高度（像素）
            max_width_inches: 最大宽度（英寸）
            
        Returns:
            (宽度, 高度) 元组（英寸）
        """
        # 假设 DPI 为 96
        dpi = 96
        width_inches = original_width / dpi
        height_inches = original_height / dpi
        
        # 如果宽度超过最大值，按比例缩小
        if width_inches > max_width_inches:
            ratio = max_width_inches / width_inches
            width_inches = max_width_inches
            height_inches = height_inches * ratio
        
        return (width_inches, height_inches)


if __name__ == "__main__":
    # 测试代码
    from ..utils.logger import setup_logger
    setup_logger()
    
    # 测试 Alt 文本提取
    test_path = "C:/Images/Dyson-V12-实测.jpg"
    alt_text = ImageProcessor.get_image_alt_text(test_path)
    logger.info(f"Alt 文本: {alt_text}")
    
    # 测试循环获取
    image_list = ["img1.jpg", "img2.jpg", "img3.jpg"]
    for i in range(10):
        img = ImageProcessor.get_cyclic_image(image_list, i)
        logger.info(f"索引 {i} -> {img}")
    
    # 测试尺寸计算
    width, height = ImageProcessor.calculate_word_image_size(1920, 1080)
    logger.info(f"Word 图片尺寸: {width:.2f} x {height:.2f} 英寸")

