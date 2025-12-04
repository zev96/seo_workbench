"""
数据库迁移脚本
用于更新已存在的数据库表结构，添加新字段
"""

import sqlite3
from loguru import logger


def migrate_database(db_path: str):
    """
    执行数据库迁移
    
    Args:
        db_path: 数据库文件路径
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("开始数据库迁移...")
        
        # 迁移 1: 为 zhihu_monitor_configs 表添加新字段（v2.3）
        _migrate_zhihu_config_v2_3(cursor, conn)
        
        # 迁移 2: 为 zhihu_monitor_tasks 表添加温和模式字段（如果之前缺失）
        _migrate_zhihu_tasks_gentle_mode(cursor, conn)
        
        # 迁移 3: 为 zhihu_monitor_tasks 表添加问题描述字段
        _migrate_zhihu_tasks_question_detail(cursor, conn)
        
        conn.close()
        logger.success("数据库迁移完成")
        
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        if conn:
            conn.rollback()
            conn.close()


def _migrate_zhihu_config_v2_3(cursor, conn):
    """
    迁移 zhihu_monitor_configs 表 - 添加 v2.3 新字段
    
    新增字段：
    - chromedriver_path: ChromeDriver 可执行文件路径
    - anti_detect_level: 反检测强度（low/medium/high）
    """
    try:
        # 检查 chromedriver_path 列是否存在
        cursor.execute("PRAGMA table_info(zhihu_monitor_configs)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # 添加 chromedriver_path 列
        if 'chromedriver_path' not in columns:
            logger.info("添加字段: zhihu_monitor_configs.chromedriver_path")
            cursor.execute("""
                ALTER TABLE zhihu_monitor_configs 
                ADD COLUMN chromedriver_path VARCHAR(500)
            """)
            conn.commit()
            logger.success("✅ 已添加字段: chromedriver_path")
        else:
            logger.info("字段已存在: chromedriver_path（跳过）")
        
        # 添加 anti_detect_level 列
        if 'anti_detect_level' not in columns:
            logger.info("添加字段: zhihu_monitor_configs.anti_detect_level")
            cursor.execute("""
                ALTER TABLE zhihu_monitor_configs 
                ADD COLUMN anti_detect_level VARCHAR(20) DEFAULT 'medium'
            """)
            conn.commit()
            logger.success("✅ 已添加字段: anti_detect_level")
        else:
            logger.info("字段已存在: anti_detect_level（跳过）")
            
    except Exception as e:
        logger.error(f"迁移 zhihu_monitor_configs 失败: {e}")
        raise


def _migrate_zhihu_tasks_gentle_mode(cursor, conn):
    """
    迁移 zhihu_monitor_tasks 表 - 确保 gentle_mode 字段存在
    
    这是为了兼容旧版本，新版本已经在 models.py 中定义了该字段
    """
    try:
        # 检查 gentle_mode 列是否存在
        cursor.execute("PRAGMA table_info(zhihu_monitor_tasks)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'gentle_mode' not in columns:
            logger.info("添加字段: zhihu_monitor_tasks.gentle_mode")
            cursor.execute("""
                ALTER TABLE zhihu_monitor_tasks 
                ADD COLUMN gentle_mode INTEGER DEFAULT 0
            """)
            conn.commit()
            logger.success("✅ 已添加字段: gentle_mode")
        else:
            logger.info("字段已存在: gentle_mode（跳过）")
            
    except Exception as e:
        logger.warning(f"迁移 zhihu_monitor_tasks.gentle_mode 失败（可能表不存在）: {e}")


def _migrate_zhihu_tasks_question_detail(cursor, conn):
    """
    迁移 zhihu_monitor_tasks 表 - 添加问题描述字段
    
    新增字段：
    - question_detail: 问题描述/补充说明
    """
    try:
        # 检查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='zhihu_monitor_tasks'
        """)
        
        if not cursor.fetchone():
            logger.info("zhihu_monitor_tasks 表不存在（跳过迁移）")
            return
        
        # 检查 question_detail 列是否存在
        cursor.execute("PRAGMA table_info(zhihu_monitor_tasks)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'question_detail' not in columns:
            logger.info("添加字段: zhihu_monitor_tasks.question_detail")
            cursor.execute("""
                ALTER TABLE zhihu_monitor_tasks 
                ADD COLUMN question_detail TEXT
            """)
            conn.commit()
            logger.success("✅ 已添加字段: question_detail")
        else:
            logger.info("字段已存在: question_detail（跳过）")
            
    except Exception as e:
        logger.warning(f"迁移 zhihu_monitor_tasks.question_detail 失败: {e}")


def check_migration_needed(db_path: str) -> bool:
    """
    检查是否需要执行迁移
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        是否需要迁移
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查 zhihu_monitor_configs 表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='zhihu_monitor_configs'
        """)
        
        if not cursor.fetchone():
            conn.close()
            return False  # 表不存在，不需要迁移（会在 create_tables 时创建）
        
        # 检查是否缺少新字段
        cursor.execute("PRAGMA table_info(zhihu_monitor_configs)")
        columns = [row[1] for row in cursor.fetchall()]
        
        needs_migration = ('chromedriver_path' not in columns or 
                          'anti_detect_level' not in columns)
        
        # 检查 zhihu_monitor_tasks 表的新字段
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='zhihu_monitor_tasks'
        """)
        
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(zhihu_monitor_tasks)")
            task_columns = [row[1] for row in cursor.fetchall()]
            needs_migration = needs_migration or 'question_detail' not in task_columns
        
        conn.close()
        
        return needs_migration
        
    except Exception as e:
        logger.error(f"检查迁移状态失败: {e}")
        return False


if __name__ == "__main__":
    # 测试迁移脚本
    import sys
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = "assets.db"
    
    print(f"测试数据库迁移: {db_path}")
    
    if check_migration_needed(db_path):
        print("需要执行迁移")
        migrate_database(db_path)
    else:
        print("不需要迁移或表不存在")

