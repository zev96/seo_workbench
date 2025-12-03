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


class ContentFingerprint(Base):
    """内容指纹表（全局历史查重）"""
    
    __tablename__ = 'content_fingerprints'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增主键')
    fingerprint = Column(String(20), nullable=False, index=True, comment='SimHash 指纹（64-bit整数转字符串）')
    content_preview = Column(String(200), comment='内容预览（前100字）')
    full_content_hash = Column(String(32), comment='全文MD5哈希（用于精确匹配）')
    source_project = Column(String(100), comment='来源项目/类目')
    document_path = Column(String(500), comment='文档路径（相对路径）')
    word_count = Column(Integer, default=0, comment='字数统计')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 索引定义
    __table_args__ = (
        Index('idx_fingerprint', 'fingerprint'),
        Index('idx_source_project', 'source_project'),
        Index('idx_created_at', 'created_at'),
        Index('idx_project_fingerprint', 'source_project', 'fingerprint'),  # 复合索引
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'fingerprint': self.fingerprint,
            'content_preview': self.content_preview,
            'full_content_hash': self.full_content_hash,
            'source_project': self.source_project,
            'document_path': self.document_path,
            'word_count': self.word_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ZhihuBrand(Base):
    """知乎监测品牌词库表"""
    
    __tablename__ = 'zhihu_brands'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增主键')
    name = Column(String(100), nullable=False, unique=True, comment='品牌名称')
    brand_type = Column(String(20), default='competitor', comment='品牌类型: own=我方, competitor=竞品')
    regex_pattern = Column(String(200), comment='正则表达式匹配模式（可选）')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    __table_args__ = (
        Index('idx_brand_type', 'brand_type'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'brand_type': self.brand_type,
            'regex_pattern': self.regex_pattern,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ZhihuMonitorTask(Base):
    """知乎监测任务表"""
    
    __tablename__ = 'zhihu_monitor_tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增主键')
    question_url = Column(String(500), nullable=False, comment='知乎问题URL')
    question_title = Column(String(200), comment='问题标题')
    target_brand = Column(String(100), nullable=False, comment='目标品牌词（我方）')
    check_range = Column(Integer, default=20, comment='检测范围（Top N）')
    
    # 当前状态
    status = Column(String(20), default='pending', comment='状态: pending/success/failed')
    last_result = Column(Text, comment='最后结果（JSON: 排名数组）')
    top10_snapshot = Column(Text, comment='Top10详细快照（JSON）')
    total_views = Column(Integer, default=0, comment='浏览量')
    total_followers = Column(Integer, default=0, comment='关注者数')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='最后更新时间')
    last_check_at = Column(DateTime, comment='最后检测时间')
    
    # 定时任务配置
    schedule_enabled = Column(Integer, default=0, comment='是否启用定时: 0=否 1=是')
    schedule_time = Column(String(10), comment='定时时间（HH:MM格式）')
    
    # 关联关系
    histories = relationship("ZhihuMonitorHistory", back_populates="task", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_question_url', 'question_url'),
        Index('idx_status', 'status'),
        Index('idx_schedule', 'schedule_enabled', 'schedule_time'),
    )
    
    def get_result_list(self):
        """获取结果排名列表"""
        try:
            return json.loads(self.last_result) if self.last_result else []
        except:
            return []
    
    def set_result_list(self, result_list):
        """设置结果排名列表"""
        self.last_result = json.dumps(result_list, ensure_ascii=False)
    
    def get_snapshot(self):
        """获取Top10快照"""
        try:
            return json.loads(self.top10_snapshot) if self.top10_snapshot else {}
        except:
            return {}
    
    def set_snapshot(self, snapshot_dict):
        """设置Top10快照"""
        self.top10_snapshot = json.dumps(snapshot_dict, ensure_ascii=False, indent=2)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'question_url': self.question_url,
            'question_title': self.question_title,
            'target_brand': self.target_brand,
            'check_range': self.check_range,
            'status': self.status,
            'last_result': self.get_result_list(),
            'total_views': self.total_views,
            'total_followers': self.total_followers,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_check_at': self.last_check_at.isoformat() if self.last_check_at else None,
            'schedule_enabled': self.schedule_enabled,
            'schedule_time': self.schedule_time
        }


class ZhihuMonitorHistory(Base):
    """知乎监测历史记录表"""
    
    __tablename__ = 'zhihu_monitor_histories'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增主键')
    task_id = Column(Integer, ForeignKey('zhihu_monitor_tasks.id'), nullable=False, comment='任务ID')
    check_result = Column(Text, comment='检测结果（JSON: 排名数组）')
    total_views = Column(Integer, default=0, comment='浏览量快照')
    total_followers = Column(Integer, default=0, comment='关注者快照')
    snapshot_data = Column(Text, comment='Top10快照数据（JSON）')
    check_at = Column(DateTime, default=datetime.now, comment='检测时间')
    
    # 关联关系
    task = relationship("ZhihuMonitorTask", back_populates="histories")
    
    __table_args__ = (
        Index('idx_task_check', 'task_id', 'check_at'),
    )
    
    def get_result_list(self):
        """获取结果排名列表"""
        try:
            return json.loads(self.check_result) if self.check_result else []
        except:
            return []
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'check_result': self.get_result_list(),
            'total_views': self.total_views,
            'total_followers': self.total_followers,
            'check_at': self.check_at.isoformat() if self.check_at else None
        }


class ZhihuMonitorConfig(Base):
    """知乎监测配置表（单例）"""
    
    __tablename__ = 'zhihu_monitor_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增主键')
    cookie = Column(Text, comment='知乎Cookie')
    user_agent = Column(String(500), comment='User-Agent（可选）')
    request_delay_min = Column(Integer, default=2, comment='请求最小间隔（秒）')
    request_delay_max = Column(Integer, default=6, comment='请求最大间隔（秒）')
    retry_count = Column(Integer, default=3, comment='失败重试次数')
    retry_delay = Column(Integer, default=600, comment='重试间隔（秒）')
    gentle_mode = Column(Integer, default=0, comment='温和模式: 0=否 1=是')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'cookie': self.cookie,
            'user_agent': self.user_agent,
            'request_delay_min': self.request_delay_min,
            'request_delay_max': self.request_delay_max,
            'retry_count': self.retry_count,
            'retry_delay': self.retry_delay,
            'gentle_mode': self.gentle_mode,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }