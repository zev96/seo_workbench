"""
SimHash 查重引擎
基于 SimHash 算法实现内容相似度检测
"""

import hashlib
import re
from typing import List, Tuple
from loguru import logger


class SimHashEngine:
    """SimHash 算法引擎"""
    
    def __init__(self, hash_bits: int = 64):
        """
        初始化 SimHash 引擎
        
        Args:
            hash_bits: 哈希位数（默认64位）
        """
        self.hash_bits = hash_bits
    
    def calculate_simhash(self, text: str) -> int:
        """
        计算文本的 SimHash 值
        
        Args:
            text: 输入文本
            
        Returns:
            SimHash 值（64-bit 整数）
        """
        if not text or not text.strip():
            return 0
        
        # 1. 分词（简单按字符分割，也可以使用 jieba 分词）
        tokens = self._tokenize(text)
        
        if not tokens:
            return 0
        
        # 2. 初始化向量（64维）
        vector = [0] * self.hash_bits
        
        # 3. 对每个词计算哈希并累加
        for token in tokens:
            # 计算词的哈希值
            token_hash = self._hash_token(token)
            
            # 根据哈希值的每一位更新向量
            for i in range(self.hash_bits):
                bit = (token_hash >> i) & 1
                if bit == 1:
                    vector[i] += 1
                else:
                    vector[i] -= 1
        
        # 4. 降维：将向量转为二进制指纹
        fingerprint = 0
        for i in range(self.hash_bits):
            if vector[i] > 0:
                fingerprint |= (1 << i)
        
        logger.debug(f"SimHash 计算: 文本长度={len(text)}, 分词数={len(tokens)}, 指纹={fingerprint}")
        return fingerprint
    
    def calculate_hamming_distance(self, hash1: int, hash2: int) -> int:
        """
        计算两个 SimHash 的海明距离
        
        Args:
            hash1: 第一个哈希值
            hash2: 第二个哈希值
            
        Returns:
            海明距离（0-64）
        """
        xor_result = hash1 ^ hash2
        distance = bin(xor_result).count('1')
        return distance
    
    def calculate_similarity(self, hash1: int, hash2: int) -> float:
        """
        计算相似度（百分比）
        
        Args:
            hash1: 第一个哈希值
            hash2: 第二个哈希值
            
        Returns:
            相似度（0.0-1.0）
        """
        distance = self.calculate_hamming_distance(hash1, hash2)
        similarity = 1.0 - (distance / self.hash_bits)
        return similarity
    
    def is_similar(
        self,
        hash1: int,
        hash2: int,
        threshold: float = 0.9
    ) -> Tuple[bool, float]:
        """
        判断两个哈希是否相似
        
        Args:
            hash1: 第一个哈希值
            hash2: 第二个哈希值
            threshold: 相似度阈值（默认0.9，即90%）
            
        Returns:
            (is_similar, similarity)
        """
        similarity = self.calculate_similarity(hash1, hash2)
        return (similarity >= threshold, similarity)
    
    def _tokenize(self, text: str) -> List[str]:
        """
        文本分词
        
        Args:
            text: 输入文本
            
        Returns:
            词列表
        """
        # 清理文本
        text = re.sub(r'\s+', ' ', text)  # 合并空白字符
        text = text.strip()
        
        # 简单分词策略：
        # 1. 按标点符号分句
        # 2. 每句按2-3字切分（模拟中文分词）
        
        tokens = []
        
        # 按标点分句
        sentences = re.split(r'[，。！？；：、\s]+', text)
        
        for sentence in sentences:
            if not sentence:
                continue
            
            # 2-gram 切分
            for i in range(len(sentence) - 1):
                tokens.append(sentence[i:i+2])
            
            # 3-gram 切分（增加权重）
            for i in range(len(sentence) - 2):
                tokens.append(sentence[i:i+3])
        
        # 去重并保持顺序
        seen = set()
        unique_tokens = []
        for token in tokens:
            if token not in seen and len(token.strip()) > 0:
                seen.add(token)
                unique_tokens.append(token)
        
        return unique_tokens
    
    def _hash_token(self, token: str) -> int:
        """
        计算单个词的哈希值
        
        Args:
            token: 词
            
        Returns:
            64-bit 整数哈希值
        """
        # 使用 MD5 生成哈希
        md5_hash = hashlib.md5(token.encode('utf-8')).hexdigest()
        
        # 取前16个字符转为64位整数
        hash_value = int(md5_hash[:16], 16)
        
        return hash_value


class ContentDeduplicator:
    """内容查重器（集成 SimHash 和数据库）"""
    
    def __init__(self, fingerprint_manager, config: dict = None):
        """
        初始化查重器
        
        Args:
            fingerprint_manager: 指纹管理器实例
            config: 查重配置
        """
        self.fp_manager = fingerprint_manager
        self.simhash_engine = SimHashEngine()
        
        # 默认配置
        self.config = {
            'enabled': True,
            'max_distance': 6,  # 海明距离阈值（对应90%相似度）
            'max_retries': 10,  # 最大重试次数
            'retention_days': 180,  # 保留天数
        }
        
        if config:
            self.config.update(config)
    
    def calculate_content_fingerprint(self, text: str) -> Tuple[int, str]:
        """
        计算内容指纹
        
        Args:
            text: 文本内容
            
        Returns:
            (simhash_int, md5_hash)
        """
        # 计算 SimHash
        simhash_value = self.simhash_engine.calculate_simhash(text)
        
        # 计算 MD5（用于精确匹配）
        md5_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        
        return (simhash_value, md5_hash)
    
    def check_duplicate(
        self,
        text: str,
        source_project: str = None
    ) -> Tuple[bool, dict]:
        """
        检查内容是否重复
        
        Args:
            text: 文本内容
            source_project: 来源项目
            
        Returns:
            (is_duplicate, duplicate_info)
            - is_duplicate: 是否重复
            - duplicate_info: 重复信息字典
        """
        if not self.config['enabled']:
            return (False, {})
        
        # 计算指纹
        simhash_value, md5_hash = self.calculate_content_fingerprint(text)
        
        # 查重
        is_dup, record, distance = self.fp_manager.check_duplicate(
            target_fingerprint=simhash_value,
            full_content_hash=md5_hash,
            max_distance=self.config['max_distance'],
            source_project=source_project
        )
        
        duplicate_info = {}
        if is_dup and record:
            similarity = (64 - distance) / 64 * 100 if distance >= 0 else 100
            duplicate_info = {
                'record_id': record.id,
                'created_at': record.created_at,
                'source_project': record.source_project,
                'document_path': record.document_path,
                'hamming_distance': distance,
                'similarity_percent': similarity,
                'preview': record.content_preview
            }
        
        return (is_dup, duplicate_info)
    
    def add_content_fingerprint(
        self,
        text: str,
        source_project: str = "",
        document_path: str = ""
    ) -> bool:
        """
        添加内容指纹到数据库
        
        Args:
            text: 文本内容
            source_project: 来源项目
            document_path: 文档路径
            
        Returns:
            是否添加成功
        """
        try:
            # 计算指纹
            simhash_value, md5_hash = self.calculate_content_fingerprint(text)
            
            # 提取预览
            preview = text[:100]
            
            # 字数统计
            word_count = len(text)
            
            # 添加到数据库
            record = self.fp_manager.add_fingerprint(
                fingerprint=str(simhash_value),
                content_preview=preview,
                full_content_hash=md5_hash,
                source_project=source_project,
                document_path=document_path,
                word_count=word_count
            )
            
            return record is not None
            
        except Exception as e:
            logger.error(f"添加指纹失败: {e}")
            return False
    
    def clean_old_fingerprints(self) -> int:
        """
        清理旧指纹
        
        Returns:
            删除的记录数
        """
        days = self.config.get('retention_days', 180)
        return self.fp_manager.clean_old_fingerprints(days)
    
    def get_statistics(self, source_project: str = None) -> dict:
        """
        获取统计信息
        
        Args:
            source_project: 项目过滤
            
        Returns:
            统计字典
        """
        return self.fp_manager.get_statistics(source_project)


def distance_to_similarity(distance: int, hash_bits: int = 64) -> float:
    """
    海明距离转相似度
    
    Args:
        distance: 海明距离
        hash_bits: 哈希位数
        
    Returns:
        相似度（0.0-1.0）
    """
    return 1.0 - (distance / hash_bits)


def similarity_to_distance(similarity: float, hash_bits: int = 64) -> int:
    """
    相似度转海明距离
    
    Args:
        similarity: 相似度（0.0-1.0）
        hash_bits: 哈希位数
        
    Returns:
        海明距离
    """
    return int((1.0 - similarity) * hash_bits)


if __name__ == "__main__":
    # 测试代码
    from ..utils.logger import setup_logger
    
    setup_logger()
    
    # 测试 SimHash
    engine = SimHashEngine()
    
    text1 = "这是一段测试文本，用于计算 SimHash 值。"
    text2 = "这是一段测试文本，用于计算 SimHash 数值。"
    text3 = "完全不同的内容，没有任何相似之处。"
    
    hash1 = engine.calculate_simhash(text1)
    hash2 = engine.calculate_simhash(text2)
    hash3 = engine.calculate_simhash(text3)
    
    logger.info(f"文本1哈希: {hash1}")
    logger.info(f"文本2哈希: {hash2}")
    logger.info(f"文本3哈希: {hash3}")
    
    dist_12 = engine.calculate_hamming_distance(hash1, hash2)
    dist_13 = engine.calculate_hamming_distance(hash1, hash3)
    
    logger.info(f"文本1和2的距离: {dist_12}, 相似度: {(64-dist_12)/64*100:.2f}%")
    logger.info(f"文本1和3的距离: {dist_13}, 相似度: {(64-dist_13)/64*100:.2f}%")

