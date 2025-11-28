"""
配置模型定义
使用 Pydantic 进行配置校验和管理
"""

import json
import os
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from loguru import logger


class APIConfig(BaseModel):
    """AI API 配置"""
    
    base_url: str = Field(default="https://api.deepseek.com", description="API 基础 URL")
    api_key: str = Field(default="", description="API 密钥")
    model: str = Field(default="deepseek-chat", description="模型名称")
    timeout: int = Field(default=30, ge=5, le=120, description="请求超时时间（秒）")
    max_retries: int = Field(default=3, ge=0, le=10, description="最大重试次数")
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        """验证 API Key 格式"""
        if v and not v.startswith('sk-'):
            logger.warning("API Key 格式可能不正确，通常应以 'sk-' 开头")
        return v


class ColumnSetting(BaseModel):
    """列设置"""
    
    col_index: int = Field(ge=0, description="列索引")
    type: str = Field(description="列类型")
    name: str = Field(default="", description="列名称")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """验证列类型"""
        valid_types = ['H1', 'H2', 'H3', 'H4', 'Body', 'List', 'Ignore']
        if v not in valid_types:
            raise ValueError(f"列类型必须是以下之一: {', '.join(valid_types)}")
        return v


class ShufflingStrategy(BaseModel):
    """混排策略配置"""
    
    name: str = Field(description="策略名称")
    columns: List[int] = Field(description="涉及的列索引列表")
    group_size: int = Field(ge=1, description="每组列数")
    keep_count: int = Field(ge=1, description="保留组数")
    shuffle_order: bool = Field(default=False, description="是否打乱顺序")
    
    @field_validator('columns')
    @classmethod
    def validate_columns(cls, v):
        """验证列索引列表"""
        if not v:
            raise ValueError("列索引列表不能为空")
        if len(v) != len(set(v)):
            raise ValueError("列索引列表中存在重复项")
        if any(col < 0 for col in v):
            raise ValueError("列索引不能为负数")
        return sorted(v)
    
    @model_validator(mode='after')
    def validate_keep_count(self):
        """验证保留组数不能超过最大组数"""
        max_groups = len(self.columns) // self.group_size
        if self.keep_count > max_groups:
            raise ValueError(
                f"保留组数 ({self.keep_count}) 不能超过最大组数 ({max_groups})"
            )
        return self


class ProfileConfig(BaseModel):
    """用户配置（根配置）"""
    
    api_config: APIConfig = Field(default_factory=APIConfig, description="API 配置")
    template_path: Optional[str] = Field(default=None, description="Word 模板路径")
    column_settings: List[ColumnSetting] = Field(default_factory=list, description="列设置")
    image_paths: Dict[str, str] = Field(default_factory=dict, description="图片文件夹路径映射")
    column_images: Dict[int, List[str]] = Field(default_factory=dict, description="列图片组映射 {列索引: [图片路径列表]}")
    bold_keywords: List[str] = Field(default_factory=list, description="加粗关键词列表")
    shuffling_strategies: List[ShufflingStrategy] = Field(
        default_factory=list,
        description="混排策略列表"
    )
    
    # 生成设置
    strict_unique: bool = Field(default=True, description="严格去重")
    output_directory: str = Field(default="output", description="输出目录")
    
    # 内容质量控制（查重评分）
    quality_check_enabled: bool = Field(default=True, description="启用内容质量检查")
    quality_threshold_premium: float = Field(default=0.2, ge=0.0, le=1.0, description="优质内容阈值（重复率 < 20%）")
    quality_threshold_standard: float = Field(default=0.5, ge=0.0, le=1.0, description="中等内容阈值（重复率 <= 50%）")
    quality_generate_report: bool = Field(default=True, description="生成质量报告 CSV")
    
    # SEO 关键词密度检查
    target_keywords: List[str] = Field(default_factory=list, description="SEO 目标关键词列表")
    seo_density_min: float = Field(default=0.01, ge=0.0, le=1.0, description="关键词密度最小值（默认 1%）")
    seo_density_max: float = Field(default=0.03, ge=0.0, le=1.0, description="关键词密度最大值（默认 3%）")
    seo_check_enabled: bool = Field(default=True, description="启用 SEO 密度检查")
    
    @field_validator('template_path')
    @classmethod
    def validate_template_path(cls, v):
        """验证模板路径"""
        if v and not os.path.exists(v):
            logger.warning(f"模板文件不存在: {v}")
        return v
    
    @field_validator('image_paths')
    @classmethod
    def validate_image_paths(cls, v):
        """验证图片路径"""
        for col_idx, path in v.items():
            if not os.path.exists(path):
                logger.warning(f"图片文件夹不存在: {path} (列 {col_idx})")
        return v
    
    def save_to_file(self, file_path: str):
        """
        保存配置到文件
        
        Args:
            file_path: 配置文件路径
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.model_dump(), f, ensure_ascii=False, indent=2)
            logger.info(f"配置已保存到: {file_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise
    
    def save_config(self, file_path: str = "profile.json"):
        """
        保存配置到默认文件
        
        Args:
            file_path: 配置文件路径（默认为 profile.json）
        """
        self.save_to_file(file_path)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'ProfileConfig':
        """
        从文件加载配置
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            ProfileConfig 实例
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"配置文件不存在: {file_path}，使用默认配置")
                return cls()
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            config = cls(**data)
            logger.info(f"配置已加载: {file_path}")
            return config
            
        except Exception as e:
            logger.error(f"加载配置失败: {e}，使用默认配置")
            return cls()
    
    def get_column_type(self, col_index: int) -> str:
        """
        获取指定列的类型
        
        Args:
            col_index: 列索引
            
        Returns:
            列类型（默认为 'Body'）
        """
        for setting in self.column_settings:
            if setting.col_index == col_index:
                return setting.type
        return 'Body'
    
    def set_column_type(self, col_index: int, col_type: str, col_name: str = ""):
        """
        设置列类型
        
        Args:
            col_index: 列索引
            col_type: 列类型
            col_name: 列名称
        """
        # 查找是否已存在
        for setting in self.column_settings:
            if setting.col_index == col_index:
                setting.type = col_type
                setting.name = col_name
                return
        
        # 不存在则添加
        self.column_settings.append(
            ColumnSetting(col_index=col_index, type=col_type, name=col_name)
        )
    
    def get_image_path(self, col_index: int) -> Optional[str]:
        """
        获取指定列的图片路径
        
        Args:
            col_index: 列索引
            
        Returns:
            图片路径或 None
        """
        return self.image_paths.get(str(col_index))
    
    def set_image_path(self, col_index: int, path: str):
        """
        设置列的图片路径
        
        Args:
            col_index: 列索引
            path: 图片文件夹路径
        """
        self.image_paths[str(col_index)] = path
    
    def add_strategy(self, strategy: ShufflingStrategy):
        """
        添加混排策略（会检查冲突）
        
        Args:
            strategy: 策略对象
            
        Raises:
            ValueError: 如果存在列冲突
        """
        # 检查冲突
        existing_columns = set()
        for s in self.shuffling_strategies:
            existing_columns.update(s.columns)
        
        new_columns = set(strategy.columns)
        conflicts = existing_columns & new_columns
        
        if conflicts:
            raise ValueError(f"策略冲突：列 {conflicts} 已被其他策略使用")
        
        self.shuffling_strategies.append(strategy)
    
    def remove_strategy(self, strategy_name: str) -> bool:
        """
        删除混排策略
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            是否删除成功
        """
        for i, strategy in enumerate(self.shuffling_strategies):
            if strategy.name == strategy_name:
                self.shuffling_strategies.pop(i)
                return True
        return False


def create_default_config() -> ProfileConfig:
    """
    创建默认配置
    
    Returns:
        默认的 ProfileConfig 实例
    """
    return ProfileConfig(
        api_config=APIConfig(),
        column_settings=[
            ColumnSetting(col_index=0, type='H1', name='标题'),
        ],
        bold_keywords=['吸力', '续航', '除螨', '智能'],
        output_directory='output'
    )


if __name__ == "__main__":
    # 测试代码
    from ..utils.logger import setup_logger
    setup_logger()
    
    # 创建默认配置
    config = create_default_config()
    
    # 添加策略
    strategy1 = ShufflingStrategy(
        name="品牌词组",
        columns=[2, 3, 4, 5],
        group_size=2,
        keep_count=1,
        shuffle_order=True
    )
    config.add_strategy(strategy1)
    
    # 保存配置
    config.save_to_file("test_profile.json")
    
    # 加载配置
    loaded_config = ProfileConfig.load_from_file("test_profile.json")
    print(f"加载的配置: {loaded_config.model_dump_json(indent=2)}")

