"""
数据校验工具
提供各种数据验证函数
"""

import os
import re
from typing import Optional
from loguru import logger


def validate_config(config_data: dict) -> tuple[bool, Optional[str]]:
    """
    验证配置数据的基本结构
    
    Args:
        config_data: 配置字典
        
    Returns:
        (是否有效, 错误信息)
    """
    required_keys = ['api_config', 'column_settings', 'image_paths']
    
    for key in required_keys:
        if key not in config_data:
            return False, f"缺少必需字段: {key}"
    
    return True, None


def validate_api_key(api_key: str) -> bool:
    """
    验证 API Key 格式
    
    Args:
        api_key: API 密钥
        
    Returns:
        是否有效
    """
    if not api_key:
        return False
    
    # 通常 API Key 以 sk- 开头
    if not api_key.startswith('sk-'):
        logger.warning("API Key 格式可能不正确")
        return False
    
    # 长度检查
    if len(api_key) < 20:
        logger.warning("API Key 长度过短")
        return False
    
    return True


def validate_file_path(file_path: str, must_exist: bool = True) -> bool:
    """
    验证文件路径
    
    Args:
        file_path: 文件路径
        must_exist: 是否必须存在
        
    Returns:
        是否有效
    """
    if not file_path:
        return False
    
    if must_exist and not os.path.exists(file_path):
        logger.warning(f"文件不存在: {file_path}")
        return False
    
    return True


def validate_directory_path(dir_path: str, must_exist: bool = True) -> bool:
    """
    验证目录路径
    
    Args:
        dir_path: 目录路径
        must_exist: 是否必须存在
        
    Returns:
        是否有效
    """
    if not dir_path:
        return False
    
    if must_exist and not os.path.isdir(dir_path):
        logger.warning(f"目录不存在: {dir_path}")
        return False
    
    return True


def validate_spintax(text: str) -> bool:
    """
    验证 Spintax 语法是否正确
    
    Args:
        text: 文本内容
        
    Returns:
        是否有效
    """
    # 检查大括号是否匹配
    if text.count('{') != text.count('}'):
        return False
    
    # 检查 Spintax 格式 {A|B|C}
    pattern = r'\{[^{}]+\}'
    matches = re.findall(pattern, text)
    
    for match in matches:
        # 检查是否包含 |
        if '|' not in match:
            return False
        
        # 检查选项是否为空
        options = match[1:-1].split('|')
        if any(not opt.strip() for opt in options):
            return False
    
    return True


def validate_column_index(col_index: int, max_columns: int) -> bool:
    """
    验证列索引
    
    Args:
        col_index: 列索引
        max_columns: 最大列数
        
    Returns:
        是否有效
    """
    return 0 <= col_index < max_columns


def validate_url(url: str) -> bool:
    """
    验证 URL 格式
    
    Args:
        url: URL 字符串
        
    Returns:
        是否有效
    """
    if not url:
        return False
    
    # 简单的 URL 格式检查
    pattern = r'^https?://.+'
    return bool(re.match(pattern, url))


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
    """
    # Windows 文件名非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    cleaned = re.sub(illegal_chars, '_', filename)
    
    # 移除首尾空格和点
    cleaned = cleaned.strip('. ')
    
    # 如果为空，使用默认名称
    if not cleaned:
        cleaned = 'untitled'
    
    return cleaned


def validate_positive_int(value: int, min_value: int = 1) -> bool:
    """
    验证正整数
    
    Args:
        value: 值
        min_value: 最小值
        
    Returns:
        是否有效
    """
    return isinstance(value, int) and value >= min_value


def validate_keyword_list(keywords: list) -> bool:
    """
    验证关键词列表
    
    Args:
        keywords: 关键词列表
        
    Returns:
        是否有效
    """
    if not isinstance(keywords, list):
        return False
    
    # 检查是否有空关键词
    return all(isinstance(kw, str) and kw.strip() for kw in keywords)


if __name__ == "__main__":
    # 测试代码
    from .logger import setup_logger
    setup_logger()
    
    # 测试 Spintax 验证
    valid_spintax = "这是{一个|一条}测试{文本|内容}"
    invalid_spintax = "这是{一个测试{文本"
    
    print(f"有效的 Spintax: {validate_spintax(valid_spintax)}")
    print(f"无效的 Spintax: {validate_spintax(invalid_spintax)}")
    
    # 测试文件名清理
    dirty_filename = 'test<file>:name?.docx'
    clean_filename = sanitize_filename(dirty_filename)
    print(f"清理后的文件名: {clean_filename}")

