"""
智能列表重排序模块
自动检测、清洗并重新生成各种格式的序号
"""
import re
from typing import Tuple, Optional
from loguru import logger


class SmartNumbering:
    """智能序号处理器"""
    
    # 中文数字映射
    CHINESE_NUMBERS = {
        1: '一', 2: '二', 3: '三', 4: '四', 5: '五',
        6: '六', 7: '七', 8: '八', 9: '九', 10: '十',
        11: '十一', 12: '十二', 13: '十三', 14: '十四', 15: '十五',
        16: '十六', 17: '十七', 18: '十八', 19: '十九', 20: '二十'
    }
    
    # 序号类型（\s* 改为 \s? 以支持无空格的情况）
    NUMBER_STYLES = {
        'arabic_dot': r'^\s*(\d+)\.\s?',          # 1. 或 1.文字（可以没有空格）
        'arabic_comma': r'^\s*(\d+)、\s?',        # 1、或 1、文字
        'arabic_colon': r'^\s*(\d+)[：:]\s?',     # 1: 或 1：或 1:文字
        'arabic_paren': r'^\s*\((\d+)\)\s?',      # (1) 或 (1)文字
        'arabic_bracket': r'^\s*\[(\d+)\]\s?',    # [1] 或 [1]文字
        'chinese_comma': r'^\s*([一二三四五六七八九十]+)、\s?',  # 一、或 一、文字
        'chinese_dot': r'^\s*([一二三四五六七八九十]+)\.\s?',    # 一. 或 一.文字
        'chinese_paren': r'^\s*[（(]([一二三四五六七八九十]+)[）)]\s?',  # （一）或（一）文字
        'chinese_bracket': r'^\s*[【\[]([一二三四五六七八九十]+)[】\]]\s?',  # 【一】或【一】文字
        'top_space': r'^\s*Top\s+(\d+)[.\s]?\s?',  # Top 1. 或 Top 1 或 Top 1文字
        'no_dot': r'^\s*No\.?\s*(\d+)\s?',        # No.1 或 No 1 或 No.1文字
        'rank': r'^\s*第([一二三四五六七八九十\d]+)[名点]\s?',  # 第一名 或 第1点 或 第一名文字
    }
    
    def __init__(self):
        """初始化"""
        pass
    
    @staticmethod
    def detect_and_clean(text: str) -> Tuple[str, Optional[str]]:
        """
        检测并清洗文本开头的序号
        
        Args:
            text: 原始文本
            
        Returns:
            (清洗后的文本, 检测到的序号类型)
        """
        if not text or not text.strip():
            return text, None
        
        # 尝试匹配所有序号类型
        for style_name, pattern in SmartNumbering.NUMBER_STYLES.items():
            match = re.match(pattern, text)
            if match:
                # 提取序号后的正文
                cleaned_text = text[match.end():]
                logger.info(f"[智能序号] 检测到: {style_name}, 原序号={match.group(1)}, 原文='{text[:30]}'")
                return cleaned_text.lstrip(), style_name
        
        # 没有匹配到序号
        logger.info(f"[智能序号] 未检测到序号: '{text[:30]}'")
        return text, None
    
    @staticmethod
    def to_chinese_number(num: int) -> str:
        """
        将阿拉伯数字转换为中文数字
        
        Args:
            num: 阿拉伯数字 (1-20)
            
        Returns:
            中文数字字符串
        """
        return SmartNumbering.CHINESE_NUMBERS.get(num, str(num))
    
    @staticmethod
    def chinese_to_arabic(chinese: str) -> int:
        """
        将中文数字转换为阿拉伯数字
        
        Args:
            chinese: 中文数字 (如 '一', '十', '十五')
            
        Returns:
            阿拉伯数字
        """
        chinese_map = {v: k for k, v in SmartNumbering.CHINESE_NUMBERS.items()}
        return chinese_map.get(chinese, 1)
    
    @staticmethod
    def generate_prefix(index: int, style: Optional[str] = None) -> str:
        """
        根据索引和样式生成新的序号前缀
        
        Args:
            index: 序号（从1开始）
            style: 序号样式类型
            
        Returns:
            格式化的序号前缀
        """
        if not style:
            # 默认使用阿拉伯数字 + 点
            return f"{index}. "
        
        if style == 'arabic_dot':
            return f"{index}. "
        elif style == 'arabic_comma':
            return f"{index}、"
        elif style == 'arabic_colon':
            return f"{index}："
        elif style == 'arabic_paren':
            return f"({index}) "
        elif style == 'arabic_bracket':
            return f"[{index}] "
        elif style == 'chinese_comma':
            return f"{SmartNumbering.to_chinese_number(index)}、"
        elif style == 'chinese_dot':
            return f"{SmartNumbering.to_chinese_number(index)}. "
        elif style == 'chinese_paren':
            return f"（{SmartNumbering.to_chinese_number(index)}）"
        elif style == 'chinese_bracket':
            return f"【{SmartNumbering.to_chinese_number(index)}】"
        elif style == 'top_space':
            return f"Top {index} "
        elif style == 'no_dot':
            return f"No.{index} "
        elif style == 'rank':
            return f"第{SmartNumbering.to_chinese_number(index)}名 "
        else:
            # 未知样式，使用默认
            return f"{index}. "
    
    @staticmethod
    def process_text(text: str, index: int, should_renumber: bool = True) -> str:
        """
        处理文本：检测、清洗、重新编号
        
        Args:
            text: 原始文本
            index: 当前序号（从1开始）
            should_renumber: 是否需要重新编号（False 时只清洗不加号）
            
        Returns:
            处理后的文本
        """
        # 检测并清洗
        cleaned_text, detected_style = SmartNumbering.detect_and_clean(text)
        
        # 如果不需要重新编号，或者原本就没有序号，直接返回清洗后的文本
        if not should_renumber:
            return cleaned_text
        
        # 如果检测到了序号，根据原样式重新生成
        if detected_style:
            new_prefix = SmartNumbering.generate_prefix(index, detected_style)
            result = new_prefix + cleaned_text
            logger.info(f"[智能序号] 重新编号: {index}, 样式={detected_style}, 新前缀='{new_prefix}', 结果='{result[:40]}'")
            return result
        
        # 原本没有序号，不添加
        logger.info(f"[智能序号] 无序号，保持原样: '{cleaned_text[:40]}'")
        return cleaned_text
    
    @staticmethod
    def should_apply_numbering(column_type: str) -> bool:
        """
        判断该列类型是否应该应用序号重排
        
        Args:
            column_type: 列类型 ('Body', 'List', 'H1', 'H2', 'H3', 'H4', 'Ignore')
            
        Returns:
            是否应该应用序号重排
        """
        # 只对 List 类型应用序号重排
        # Body 类型只清洗不重新编号
        return column_type == 'List'

