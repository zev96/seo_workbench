"""
混排策略执行器
实现多策略混排逻辑
"""

import random
from typing import List, Dict, Set, Tuple
from loguru import logger

from ..config.settings import ShufflingStrategy


class ShuffleEngine:
    """混排策略执行器"""
    
    def __init__(self, strategies: List[ShufflingStrategy]):
        """
        初始化混排引擎
        
        Args:
            strategies: 策略列表
        """
        self.strategies = strategies
        self._validate_strategies()
    
    def _validate_strategies(self):
        """验证策略列表（检查列冲突）"""
        all_columns = []
        for strategy in self.strategies:
            all_columns.extend(strategy.columns)
        
        if len(all_columns) != len(set(all_columns)):
            duplicates = [col for col in set(all_columns) if all_columns.count(col) > 1]
            raise ValueError(f"策略冲突：列 {duplicates} 被多个策略使用")
        
        logger.info(f"混排策略验证通过，共 {len(self.strategies)} 个策略")
    
    def execute(self, total_columns: int) -> Dict[int, bool]:
        """
        执行混排策略，返回每列是否保留的映射
        
        Args:
            total_columns: 总列数
            
        Returns:
            {列索引: 是否保留} 的字典
        """
        # 默认所有列都保留
        column_keep_map = {i: True for i in range(total_columns)}
        
        # 执行每个策略
        for strategy in self.strategies:
            kept_columns = self._execute_single_strategy(strategy)
            
            # 更新保留映射
            for col in strategy.columns:
                column_keep_map[col] = col in kept_columns
        
        kept_count = sum(1 for keep in column_keep_map.values() if keep)
        logger.debug(f"混排执行完成：保留 {kept_count}/{total_columns} 列")
        
        return column_keep_map
    
    def _execute_single_strategy(self, strategy: ShufflingStrategy) -> Set[int]:
        """
        执行单个策略
        
        Args:
            strategy: 策略对象
            
        Returns:
            保留的列索引集合
        """
        columns = strategy.columns
        group_size = strategy.group_size
        keep_count = strategy.keep_count
        shuffle_order = strategy.shuffle_order
        
        # 将列切分为组
        groups = []
        for i in range(0, len(columns), group_size):
            group = columns[i:i + group_size]
            groups.append(group)
        
        # 随机抽取保留的组
        if keep_count >= len(groups):
            kept_groups = groups
        else:
            kept_groups = random.sample(groups, keep_count)
        
        # 如果需要打乱顺序
        if shuffle_order:
            random.shuffle(kept_groups)
        
        # 展开为列索引集合
        kept_columns = set()
        for group in kept_groups:
            kept_columns.update(group)
        
        logger.debug(
            f"策略 '{strategy.name}': "
            f"列 {columns} -> 切分为 {len(groups)} 组 -> "
            f"保留 {len(kept_groups)} 组 -> 列 {sorted(kept_columns)}"
        )
        
        return kept_columns
    
    def get_column_order(self, total_columns: int) -> List[int]:
        """
        获取列的最终顺序（考虑策略的乱序设置）
        
        Args:
            total_columns: 总列数
            
        Returns:
            列索引的有序列表
        """
        # 获取保留映射
        keep_map = self.execute(total_columns)
        
        # 筛选保留的列
        kept_columns = [col for col in range(total_columns) if keep_map[col]]
        
        return kept_columns
    
    @staticmethod
    def check_column_conflict(
        existing_strategies: List[ShufflingStrategy],
        new_columns: List[int]
    ) -> Tuple[bool, List[int]]:
        """
        检查新列是否与现有策略冲突
        
        Args:
            existing_strategies: 现有策略列表
            new_columns: 新列索引列表
            
        Returns:
            (是否冲突, 冲突的列索引列表)
        """
        existing_columns = set()
        for strategy in existing_strategies:
            existing_columns.update(strategy.columns)
        
        new_columns_set = set(new_columns)
        conflicts = existing_columns & new_columns_set
        
        return bool(conflicts), sorted(conflicts)


class SmartShuffle:
    """智能轮播器（优先使用未用过的素材）"""
    
    def __init__(self, total_items: int):
        """
        初始化智能轮播器
        
        Args:
            total_items: 素材总数
        """
        self.total_items = total_items
        self.used_indices = set()
        self.available_indices = list(range(total_items))
        random.shuffle(self.available_indices)
    
    def get_next_index(self) -> int:
        """
        获取下一个索引（优先未用过的）
        
        Returns:
            索引值
        """
        # 如果所有索引都用过了，重置
        if len(self.used_indices) >= self.total_items:
            self.used_indices.clear()
            self.available_indices = list(range(self.total_items))
            random.shuffle(self.available_indices)
            logger.debug("智能轮播器已重置")
        
        # 从可用索引中取出一个
        if self.available_indices:
            index = self.available_indices.pop(0)
        else:
            # 理论上不会到这里
            index = random.randint(0, self.total_items - 1)
        
        self.used_indices.add(index)
        return index
    
    def reset(self):
        """重置轮播器"""
        self.used_indices.clear()
        self.available_indices = list(range(self.total_items))
        random.shuffle(self.available_indices)


class UniqueGenerator:
    """唯一性生成器（严格去重）"""
    
    def __init__(self, max_retries: int = 5):
        """
        初始化唯一性生成器
        
        Args:
            max_retries: 最大重试次数
        """
        self.generated_combinations = set()
        self.max_retries = max_retries
    
    def is_unique(self, combination: tuple) -> bool:
        """
        检查组合是否唯一
        
        Args:
            combination: 组合元组
            
        Returns:
            是否唯一
        """
        return combination not in self.generated_combinations
    
    def add_combination(self, combination: tuple):
        """
        添加组合到已生成集合
        
        Args:
            combination: 组合元组
        """
        self.generated_combinations.add(combination)
    
    def get_unique_combination(
        self,
        generator_func,
        *args,
        **kwargs
    ) -> tuple:
        """
        生成唯一组合（带重试）
        
        Args:
            generator_func: 生成函数
            *args, **kwargs: 传递给生成函数的参数
            
        Returns:
            唯一的组合元组
            
        Raises:
            RuntimeError: 超过最大重试次数
        """
        for attempt in range(self.max_retries):
            combination = generator_func(*args, **kwargs)
            if self.is_unique(combination):
                self.add_combination(combination)
                return combination
        
        # 超过重试次数，记录警告但仍返回
        logger.warning(f"超过最大重试次数 ({self.max_retries})，可能存在重复")
        self.add_combination(combination)
        return combination
    
    def get_generated_count(self) -> int:
        """
        获取已生成的组合数量
        
        Returns:
            数量
        """
        return len(self.generated_combinations)
    
    def reset(self):
        """重置生成器"""
        self.generated_combinations.clear()


if __name__ == "__main__":
    # 测试代码
    from ..utils.logger import setup_logger
    from ..config.settings import ShufflingStrategy
    
    setup_logger()
    
    # 测试混排策略
    strategy1 = ShufflingStrategy(
        name="品牌词组",
        columns=[2, 3, 4, 5],
        group_size=2,
        keep_count=1,
        shuffle_order=True
    )
    
    strategy2 = ShufflingStrategy(
        name="竞品对比组",
        columns=[8, 9, 10],
        group_size=1,
        keep_count=2,
        shuffle_order=False
    )
    
    engine = ShuffleEngine([strategy1, strategy2])
    
    # 执行多次看结果
    for i in range(3):
        logger.info(f"\n第 {i+1} 次执行:")
        keep_map = engine.execute(total_columns=15)
        kept_cols = [col for col, keep in keep_map.items() if keep]
        logger.info(f"保留的列: {kept_cols}")
    
    # 测试智能轮播
    logger.info("\n测试智能轮播:")
    shuffler = SmartShuffle(5)
    for i in range(12):
        index = shuffler.get_next_index()
        logger.info(f"第 {i+1} 次: 索引 {index}")

