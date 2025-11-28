"""
数据库管理类
提供素材库的增删改查接口，使用单例模式
"""

import os
from typing import List, Optional
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from loguru import logger

from .models import Base, Material


class DatabaseManager:
    """数据库管理器（单例模式）"""
    
    _instance = None
    _engine = None
    _session_factory = None
    
    def __new__(cls, db_path: str = "assets.db"):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(db_path)
        return cls._instance
    
    def _initialize(self, db_path: str):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        db_url = f"sqlite:///{db_path}"
        
        # 创建引擎
        self._engine = create_engine(
            db_url,
            echo=False,  # 设为 True 可以看到 SQL 语句
            pool_pre_ping=True  # 连接池健康检查
        )
        
        # 创建会话工厂
        self._session_factory = sessionmaker(bind=self._engine)
        
        logger.info(f"数据库管理器初始化完成: {db_path}")
    
    def create_tables(self):
        """创建所有表（如果不存在）"""
        Base.metadata.create_all(self._engine)
        logger.info("数据库表创建完成")
    
    def get_session(self) -> Session:
        """
        获取数据库会话
        
        Returns:
            SQLAlchemy Session 对象
        """
        return self._session_factory()
    
    # ==================== 增 ====================
    
    def add_material(self, category: str, content: str, tags: str = None) -> Optional[Material]:
        """
        添加新素材
        
        Args:
            category: 分类名称
            content: 文本内容
            tags: 标签（可选）
            
        Returns:
            创建的 Material 对象，失败返回 None
        """
        session = self.get_session()
        try:
            # 检查是否重复
            content_hash = Material._generate_hash(content)
            existing = session.query(Material).filter(
                and_(
                    Material.category == category,
                    Material.content_hash == content_hash
                )
            ).first()
            
            if existing:
                logger.warning(f"素材已存在: {category} - {content[:20]}...")
                return None
            
            # 创建新素材
            material = Material(category=category, content=content, tags=tags)
            session.add(material)
            session.commit()
            session.refresh(material)
            
            logger.info(f"添加素材成功: ID={material.id}, 分类={category}")
            return material
            
        except Exception as e:
            session.rollback()
            logger.error(f"添加素材失败: {e}")
            return None
        finally:
            session.close()
    
    # ==================== 删 ====================
    
    def delete_material(self, material_id: int) -> bool:
        """
        删除素材
        
        Args:
            material_id: 素材 ID
            
        Returns:
            是否删除成功
        """
        session = self.get_session()
        try:
            material = session.query(Material).filter(Material.id == material_id).first()
            if material:
                session.delete(material)
                session.commit()
                logger.info(f"删除素材成功: ID={material_id}")
                return True
            else:
                logger.warning(f"素材不存在: ID={material_id}")
                return False
        except Exception as e:
            session.rollback()
            logger.error(f"删除素材失败: {e}")
            return False
        finally:
            session.close()
    
    # ==================== 改 ====================
    
    def update_material(self, material_id: int, **kwargs) -> bool:
        """
        更新素材
        
        Args:
            material_id: 素材 ID
            **kwargs: 要更新的字段（category, content, tags）
            
        Returns:
            是否更新成功
        """
        session = self.get_session()
        try:
            material = session.query(Material).filter(Material.id == material_id).first()
            if not material:
                logger.warning(f"素材不存在: ID={material_id}")
                return False
            
            # 更新字段
            if 'category' in kwargs:
                material.category = kwargs['category']
            if 'tags' in kwargs:
                material.tags = kwargs['tags']
            if 'content' in kwargs:
                material.update_content(kwargs['content'])
            
            session.commit()
            logger.info(f"更新素材成功: ID={material_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"更新素材失败: {e}")
            return False
        finally:
            session.close()
    
    def increment_usage(self, material_id: int) -> bool:
        """
        增加素材使用次数
        
        Args:
            material_id: 素材 ID
            
        Returns:
            是否更新成功
        """
        session = self.get_session()
        try:
            material = session.query(Material).filter(Material.id == material_id).first()
            if material:
                material.increment_usage()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"更新使用次数失败: {e}")
            return False
        finally:
            session.close()
    
    # ==================== 查 ====================
    
    def get_material_by_id(self, material_id: int) -> Optional[Material]:
        """
        根据 ID 获取素材
        
        Args:
            material_id: 素材 ID
            
        Returns:
            Material 对象或 None
        """
        session = self.get_session()
        try:
            return session.query(Material).filter(Material.id == material_id).first()
        finally:
            session.close()
    
    def get_materials_by_category(self, category: str) -> List[Material]:
        """
        根据分类获取素材列表
        
        Args:
            category: 分类名称
            
        Returns:
            Material 对象列表
        """
        session = self.get_session()
        try:
            return session.query(Material).filter(
                Material.category == category
            ).order_by(Material.usage_count.desc()).all()
        finally:
            session.close()
    
    def get_all_categories(self) -> List[str]:
        """
        获取所有分类名称
        
        Returns:
            分类名称列表
        """
        session = self.get_session()
        try:
            result = session.query(Material.category).distinct().all()
            return [row[0] for row in result]
        finally:
            session.close()
    
    def search_materials(self, keyword: str) -> List[Material]:
        """
        搜索素材（在内容和标签中搜索）
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的 Material 对象列表
        """
        session = self.get_session()
        try:
            search_pattern = f"%{keyword}%"
            return session.query(Material).filter(
                (Material.content.like(search_pattern)) |
                (Material.tags.like(search_pattern))
            ).all()
        finally:
            session.close()
    
    def get_all_materials(self, limit: int = None) -> List[Material]:
        """
        获取所有素材
        
        Args:
            limit: 限制数量（可选）
            
        Returns:
            Material 对象列表
        """
        session = self.get_session()
        try:
            query = session.query(Material).order_by(Material.created_at.desc())
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()
    
    # ==================== 统计 ====================
    
    def get_material_count(self) -> int:
        """
        获取素材总数
        
        Returns:
            素材数量
        """
        session = self.get_session()
        try:
            return session.query(Material).count()
        finally:
            session.close()
    
    def get_category_count(self) -> int:
        """
        获取分类总数
        
        Returns:
            分类数量
        """
        session = self.get_session()
        try:
            return session.query(Material.category).distinct().count()
        finally:
            session.close()

