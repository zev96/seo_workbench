"""
Spintax 语法解析器
支持 {A|B|C} 格式的随机替换
"""

import re
import random
from typing import List
from loguru import logger


class SpintaxParser:
    """Spintax 语法解析器"""
    
    # 匹配 {A|B|C} 格式的正则表达式
    PATTERN = r'\{([^{}]+)\}'
    
    @staticmethod
    def parse(text: str) -> str:
        """
        解析 Spintax 语法，随机选择选项
        
        Args:
            text: 包含 Spintax 语法的文本
            
        Returns:
            解析后的文本
        """
        if not text:
            return text
        
        def replace_spintax(match):
            """替换单个 Spintax 匹配"""
            options = match.group(1).split('|')
            # 过滤空选项
            options = [opt.strip() for opt in options if opt.strip()]
            if not options:
                return ''
            return random.choice(options)
        
        # 递归替换所有 Spintax
        result = text
        while re.search(SpintaxParser.PATTERN, result):
            result = re.sub(SpintaxParser.PATTERN, replace_spintax, result)
        
        return result
    
    @staticmethod
    def has_spintax(text: str) -> bool:
        """
        检查文本是否包含 Spintax 语法
        
        Args:
            text: 文本内容
            
        Returns:
            是否包含 Spintax
        """
        return bool(re.search(SpintaxParser.PATTERN, text))
    
    @staticmethod
    def get_spintax_count(text: str) -> int:
        """
        获取文本中 Spintax 的数量
        
        Args:
            text: 文本内容
            
        Returns:
            Spintax 数量
        """
        return len(re.findall(SpintaxParser.PATTERN, text))
    
    @staticmethod
    def get_spintax_options(text: str) -> List[List[str]]:
        """
        获取所有 Spintax 的选项列表
        
        Args:
            text: 文本内容
            
        Returns:
            选项列表的列表
        """
        matches = re.findall(SpintaxParser.PATTERN, text)
        return [match.split('|') for match in matches]
    
    @staticmethod
    def calculate_variations(text: str) -> int:
        """
        计算文本可能的变体数量
        
        Args:
            text: 文本内容
            
        Returns:
            变体数量
        """
        options_list = SpintaxParser.get_spintax_options(text)
        if not options_list:
            return 1
        
        # 计算所有选项数量的乘积
        variations = 1
        for options in options_list:
            variations *= len(options)
        
        return variations
    
    @staticmethod
    def validate(text: str) -> tuple[bool, str]:
        """
        验证 Spintax 语法是否正确
        
        Args:
            text: 文本内容
            
        Returns:
            (是否有效, 错误信息)
        """
        if not text:
            return True, ""
        
        # 检查大括号是否匹配
        if text.count('{') != text.count('}'):
            return False, "大括号不匹配"
        
        # 检查每个 Spintax 格式
        matches = re.finditer(SpintaxParser.PATTERN, text)
        for match in matches:
            content = match.group(1)
            
            # 检查是否包含 |
            if '|' not in content:
                return False, f"Spintax 格式错误: {{{content}}}, 缺少 '|' 分隔符"
            
            # 检查选项是否为空
            options = content.split('|')
            if any(not opt.strip() for opt in options):
                return False, f"Spintax 包含空选项: {{{content}}}"
        
        return True, ""


if __name__ == "__main__":
    # 测试代码
    from ..utils.logger import setup_logger
    setup_logger()
    
    # 测试基本解析
    text1 = "这是{一个|一条}测试{文本|内容|段落}"
    logger.info(f"原文: {text1}")
    for i in range(5):
        logger.info(f"解析 {i+1}: {SpintaxParser.parse(text1)}")
    
    # 测试变体计算
    variations = SpintaxParser.calculate_variations(text1)
    logger.info(f"可能的变体数: {variations}")
    
    # 测试验证
    valid_text = "{好的|不错的}产品"
    invalid_text = "{好的产品"
    
    is_valid, msg = SpintaxParser.validate(valid_text)
    logger.info(f"'{valid_text}' 验证结果: {is_valid}, {msg}")
    
    is_valid, msg = SpintaxParser.validate(invalid_text)
    logger.info(f"'{invalid_text}' 验证结果: {is_valid}, {msg}")

