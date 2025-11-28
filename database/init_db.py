"""
数据库初始化脚本
程序启动时调用，检查并创建数据库表
"""

import os
from loguru import logger
from .db_manager import DatabaseManager
from .models import Material


def init_database(db_path: str = "assets.db") -> DatabaseManager:
    """
    初始化数据库
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        DatabaseManager 实例
    """
    # 检查数据库文件是否存在
    db_exists = os.path.exists(db_path)
    
    if not db_exists:
        logger.info(f"数据库文件不存在，将创建新数据库: {db_path}")
    else:
        logger.info(f"数据库文件已存在: {db_path}")
    
    # 创建数据库管理器实例（单例）
    db_manager = DatabaseManager(db_path)
    
    # 创建表（如果不存在）
    db_manager.create_tables()
    
    # 如果是新数据库，添加一些示例数据
    if not db_exists:
        _add_sample_data(db_manager)
    
    # 显示统计信息
    material_count = db_manager.get_material_count()
    category_count = db_manager.get_category_count()
    logger.info(f"数据库初始化完成 - 素材数: {material_count}, 分类数: {category_count}")
    
    return db_manager


def _add_sample_data(db_manager: DatabaseManager):
    """
    添加示例数据（仅在新数据库时调用）
    
    Args:
        db_manager: 数据库管理器实例
    """
    logger.info("正在添加示例数据...")
    
    sample_materials = [
        {
            "category": "通用-开头",
            "content": "在当今快节奏的生活中，{越来越多|更多}的人开始关注{生活品质|居家环境}的提升。",
            "tags": "开头,通用"
        },
        {
            "category": "通用-开头",
            "content": "随着科技的{不断发展|持续进步}，{智能家居|现代家电}已经成为我们生活中不可或缺的一部分。",
            "tags": "开头,科技"
        },
        {
            "category": "通用-结尾",
            "content": "总的来说，这款产品{非常值得|确实值得}推荐给{追求品质|注重生活}的你。",
            "tags": "结尾,推荐"
        },
        {
            "category": "洗地机-痛点",
            "content": "传统的{拖地方式|清洁方法}不仅{费时费力|耗时耗力}，而且清洁效果往往{不尽如人意|差强人意}。",
            "tags": "痛点,洗地机"
        },
        {
            "category": "洗地机-卖点",
            "content": "强劲的{吸力|清洁能力}配合{智能感应|自动调节}系统，让清洁变得{轻松简单|省心省力}。",
            "tags": "卖点,洗地机"
        },
    ]
    
    for material_data in sample_materials:
        db_manager.add_material(
            category=material_data["category"],
            content=material_data["content"],
            tags=material_data.get("tags")
        )
    
    logger.info(f"示例数据添加完成，共 {len(sample_materials)} 条")


if __name__ == "__main__":
    # 测试代码
    from ..utils.logger import setup_logger
    setup_logger()
    
    db = init_database("test_assets.db")
    
    # 测试查询
    print("\n所有分类:")
    for cat in db.get_all_categories():
        print(f"  - {cat}")
    
    print("\n所有素材:")
    for mat in db.get_all_materials():
        print(f"  {mat}")

