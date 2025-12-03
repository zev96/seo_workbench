"""
数据库 ORM 模型定义
使用 SQLAlchemy 定义 Material 表和对比表相关表结构
"""

import hashlib
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Index, ForeignKey
from sqlalchemy.orm import relationship
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


class ComparisonCategory(Base):
    """对比表类目表"""
    
    __tablename__ = 'comparison_categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增主键')
    name = Column(String(100), nullable=False, unique=True, comment='类目名称')
    icon = Column(String(50), comment='图标名称')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关联关系
    brands = relationship("ComparisonBrand", back_populates="category", cascade="all, delete-orphan")
    parameters = relationship("ComparisonParameter", back_populates="category", cascade="all, delete-orphan")
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ComparisonBrand(Base):
    """对比表品牌表"""
    
    __tablename__ = 'comparison_brands'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增主键')
    category_id = Column(Integer, ForeignKey('comparison_categories.id'), nullable=False, comment='类目ID')
    name = Column(String(100), nullable=False, comment='品牌名称')
    is_own = Column(Integer, default=0, comment='是否为我方品牌 0=否 1=是')
    sort_order = Column(Integer, default=0, comment='排序顺序')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关联关系
    category = relationship("ComparisonCategory", back_populates="brands")
    values = relationship("ComparisonValue", back_populates="brand", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_category_brand', 'category_id', 'name'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'category_id': self.category_id,
            'name': self.name,
            'is_own': self.is_own,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ComparisonParameter(Base):
    """对比表参数表"""
    
    __tablename__ = 'comparison_parameters'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增主键')
    category_id = Column(Integer, ForeignKey('comparison_categories.id'), nullable=False, comment='类目ID')
    name = Column(String(100), nullable=False, comment='参数名称')
    sort_order = Column(Integer, default=0, comment='排序顺序')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关联关系
    category = relationship("ComparisonCategory", back_populates="parameters")
    values = relationship("ComparisonValue", back_populates="parameter", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_category_param', 'category_id', 'name'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'category_id': self.category_id,
            'name': self.name,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ComparisonValue(Base):
    """对比表数值表（参数值）"""
    
    __tablename__ = 'comparison_values'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增主键')
    category_id = Column(Integer, ForeignKey('comparison_categories.id'), nullable=False, comment='类目ID')
    brand_id = Column(Integer, ForeignKey('comparison_brands.id'), nullable=False, comment='品牌ID')
    parameter_id = Column(Integer, ForeignKey('comparison_parameters.id'), nullable=False, comment='参数ID')
    value = Column(Text, comment='参数值')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关联关系
    brand = relationship("ComparisonBrand", back_populates="values")
    parameter = relationship("ComparisonParameter", back_populates="values")
    
    __table_args__ = (
        Index('idx_brand_param', 'brand_id', 'parameter_id'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'category_id': self.category_id,
            'brand_id': self.brand_id,
            'parameter_id': self.parameter_id,
            'value': self.value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ComparisonConfig(Base):
    """对比表配置表"""
    
    __tablename__ = 'comparison_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增主键')
    config_type = Column(String(50), nullable=False, comment='配置类型: brand_match/insert_position/table_style')
    config_data = Column(Text, nullable=False, comment='配置数据(JSON格式)')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def get_config_dict(self):
        """获取配置字典"""
        try:
            return json.loads(self.config_data)
        except:
            return {}
    
    def set_config_dict(self, config_dict):
        """设置配置字典"""
        self.config_data = json.dumps(config_dict, ensure_ascii=False)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'config_type': self.config_type,
            'config_data': self.get_config_dict(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ComparisonTask(Base):
    """对比表任务表（支持多任务）"""
    
    __tablename__ = 'comparison_tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增主键')
    category_id = Column(Integer, ForeignKey('comparison_categories.id'), nullable=False, comment='类目ID')
    task_name = Column(String(100), nullable=False, comment='任务名称')
    sort_order = Column(Integer, default=0, comment='排序顺序')
    
    # 插入位置配置
    insert_mode = Column(String(20), default='column', comment='插入模式: column/anchor')
    insert_column = Column(Integer, default=1, comment='插入列号')
    insert_anchor_text = Column(String(100), comment='锚点文本')
    
    # 样式配置（JSON格式）
    style_config = Column(Text, comment='样式配置JSON')
    
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关联关系
    selected_parameters = relationship("TaskParameterSelection", back_populates="task", cascade="all, delete-orphan")
    
    def get_style_dict(self):
        """获取样式配置字典"""
        try:
            return json.loads(self.style_config) if self.style_config else {}
        except:
            return {}
    
    def set_style_dict(self, style_dict):
        """设置样式配置字典"""
        self.style_config = json.dumps(style_dict, ensure_ascii=False)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'category_id': self.category_id,
            'task_name': self.task_name,
            'sort_order': self.sort_order,
            'insert_mode': self.insert_mode,
            'insert_column': self.insert_column,
            'insert_anchor_text': self.insert_anchor_text,
            'style_config': self.get_style_dict(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class TaskParameterSelection(Base):
    """任务参数选择关联表"""
    
    __tablename__ = 'task_parameter_selections'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增主键')
    task_id = Column(Integer, ForeignKey('comparison_tasks.id'), nullable=False, comment='任务ID')
    parameter_id = Column(Integer, ForeignKey('comparison_parameters.id'), nullable=False, comment='参数ID')
    
    # 关联关系
    task = relationship("ComparisonTask", back_populates="selected_parameters")
    
    __table_args__ = (
        Index('idx_task_param', 'task_id', 'parameter_id'),
    )

