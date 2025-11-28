"""
数据库 ORM 模型定义
使用 SQLAlchemy 定义 Material 表结构
"""

import hashlib
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Material(Base):
    """素材表 ORM 模型"""
    
    __tablename__ = 'materials'
    
    # 字段定义
    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增主键')
    category = Column(Text, nullable=False, comment='分类名称')
    content = Column(Text, nullable=False, comment='文本内容')
    content_hash = Column(Text, comment='内容 MD5 哈希值')
    tags = Column(Text, comment='标签')
    usage_count = Column(Integer, default=0, comment='使用次数')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 索引定义
    __table_args__ = (
        Index('idx_category', 'category'),
        Index('idx_content_hash', 'content_hash'),
    )
    
    def __init__(self, category: str, content: str, tags: str = None):
        """
        初始化素材对象
        
        Args:
            category: 分类名称
            content: 文本内容
            tags: 标签（可选）
        """
        self.category = category
        self.content = content
        self.tags = tags
        self.content_hash = self._generate_hash(content)
        self.usage_count = 0
        self.created_at = datetime.now()
    
    @staticmethod
    def _generate_hash(content: str) -> str:
        """
        生成内容的 MD5 哈希值
        
        Args:
            content: 文本内容
            
        Returns:
            MD5 哈希字符串
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def increment_usage(self):
        """增加使用次数"""
        self.usage_count += 1
    
    def update_content(self, new_content: str):
        """
        更新内容并重新计算哈希值
        
        Args:
            new_content: 新的文本内容
        """
        self.content = new_content
        self.content_hash = self._generate_hash(new_content)
    
    def __repr__(self):
        return f"<Material(id={self.id}, category='{self.category}', usage={self.usage_count})>"
    
    def to_dict(self):
        """
        转换为字典格式
        
        Returns:
            包含所有字段的字典
        """
        return {
            'id': self.id,
            'category': self.category,
            'content': self.content,
            'content_hash': self.content_hash,
            'tags': self.tags,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

