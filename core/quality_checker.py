"""
内容质量检查器
基于 Jaccard 相似度的查重和评分系统
"""
from typing import List, Set, Tuple, Dict
from dataclasses import dataclass
from datetime import datetime
from loguru import logger


@dataclass
class QualityScore:
    """质量评分结果"""
    max_similarity: float  # 最大重复率（0-1）
    rating: str  # 评级：优质/中等/高重复
    rating_en: str  # 英文评级：Premium/Standard/Repetitive
    compared_count: int  # 对比文档数量
    
    # SEO 密度评分
    keyword_density: float = 0.0  # 关键词密度（0-1）
    density_rating: str = ""  # 密度评级：完美/不足/堆砌
    seo_suggestion: str = ""  # SEO 建议


class QualityChecker:
    """内容质量检查器"""
    
    def __init__(self, 
                 threshold_premium: float = 0.2,
                 threshold_standard: float = 0.5,
                 seo_keywords: List[str] = None,
                 seo_density_min: float = 0.01,
                 seo_density_max: float = 0.03):
        """
        初始化质量检查器
        
        Args:
            threshold_premium: 优质内容阈值（默认 0.2，即 20%）
            threshold_standard: 中等内容阈值（默认 0.5，即 50%）
            seo_keywords: SEO 目标关键词列表
            seo_density_min: 关键词密度最小值（默认 0.01，即 1%）
            seo_density_max: 关键词密度最大值（默认 0.03，即 3%）
        """
        self.threshold_premium = threshold_premium
        self.threshold_standard = threshold_standard
        self.history_fingerprints: List[Set[str]] = []  # 已生成文档的指纹集合
        
        # SEO 相关
        self.seo_keywords = seo_keywords or []
        self.seo_density_min = seo_density_min
        self.seo_density_max = seo_density_max
        
        logger.info(f"质量检查器初始化: 优质阈值={threshold_premium}, 中等阈值={threshold_standard}")
        if self.seo_keywords:
            logger.info(f"SEO 关键词: {self.seo_keywords}, 密度范围: {seo_density_min:.1%} - {seo_density_max:.1%}")
    
    def reset(self):
        """重置历史记录（开始新的批次生成时调用）"""
        self.history_fingerprints.clear()
        logger.info("质量检查器历史记录已清空")
    
    @staticmethod
    def create_fingerprint(row_data: List[str]) -> Set[str]:
        """
        创建文档指纹（段落 ID 集合）
        
        Args:
            row_data: 行数据列表，每个元素是一列的内容
            
        Returns:
            文档指纹集合（使用内容哈希）
        """
        fingerprint = set()
        
        for col_idx, content in enumerate(row_data):
            if content and content.strip():
                # 使用列索引+内容哈希作为段落ID
                # 这样可以区分不同列的相同内容
                content_hash = hash(content.strip())
                segment_id = f"{col_idx}:{content_hash}"
                fingerprint.add(segment_id)
        
        return fingerprint
    
    @staticmethod
    def count_chinese_words(text: str) -> int:
        """
        计算中文文本的字数
        
        Args:
            text: 文本内容
            
        Returns:
            字数（中文字符数 + 英文单词数）
        """
        import re
        
        # 移除标点符号和空白字符
        text = re.sub(r'[，。！？、；：""''（）《》【】\s]+', '', text)
        
        # 计算中文字符数
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        
        # 计算英文单词数（简化处理）
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        
        return chinese_chars + english_words
    
    def check_keyword_density(self, text: str) -> Tuple[float, str, str]:
        """
        检查关键词密度
        
        Args:
            text: 文章全文
            
        Returns:
            (密度, 评级, 建议)
        """
        if not self.seo_keywords or not text:
            return 0.0, "", ""
        
        # 计算总字数
        total_words = self.count_chinese_words(text)
        
        if total_words == 0:
            return 0.0, "不足", "文章内容为空"
        
        # 计算关键词出现次数
        keyword_count = 0
        keyword_total_length = 0
        
        for keyword in self.seo_keywords:
            count = text.count(keyword)
            keyword_count += count
            keyword_total_length += len(keyword) * count
        
        # 计算密度
        # 公式：(关键词总字符数) / 总字数
        if keyword_total_length == 0:
            density = 0.0
        else:
            density = keyword_total_length / total_words
        
        # 评级和建议
        if density < self.seo_density_min:
            rating = "不足"
            suggestion = "需增加关键词"
        elif density > self.seo_density_max:
            rating = "堆砌"
            suggestion = "关键词过多，建议删减"
        else:
            rating = "完美"
            suggestion = ""
        
        logger.debug(f"SEO 密度检查: 总字数={total_words}, 关键词字符数={keyword_total_length}, 密度={density:.2%}, 评级={rating}")
        
        return density, rating, suggestion
    
    @staticmethod
    def calculate_jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
        """
        计算两个集合的 Jaccard 相似度
        
        Args:
            set_a: 集合 A
            set_b: 集合 B
            
        Returns:
            Jaccard 相似度（0-1）
        """
        if not set_a and not set_b:
            return 0.0
        
        if not set_a or not set_b:
            return 0.0
        
        intersection = len(set_a & set_b)  # 交集
        union = len(set_a | set_b)  # 并集
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def check_quality(self, current_fingerprint: Set[str], full_text: str = "") -> QualityScore:
        """
        检查当前文档的质量（与历史文档对比）
        
        Args:
            current_fingerprint: 当前文档的指纹
            
        Returns:
            质量评分结果
        """
        if not self.history_fingerprints:
            # 第一篇文档，没有对比对象
            max_similarity = 0.0
        else:
            # 与所有历史文档对比，取最大相似度
            similarities = [
                self.calculate_jaccard_similarity(current_fingerprint, hist_fp)
                for hist_fp in self.history_fingerprints
            ]
            max_similarity = max(similarities)
        
        # 根据阈值判断评级
        if max_similarity < self.threshold_premium:
            rating = "优质"
            rating_en = "Premium"
        elif max_similarity <= self.threshold_standard:
            rating = "中等"
            rating_en = "Standard"
        else:
            rating = "高重复"
            rating_en = "Repetitive"
        
        # 将当前文档加入历史记录
        self.history_fingerprints.append(current_fingerprint)
        
        # SEO 密度检查
        keyword_density = 0.0
        density_rating = ""
        seo_suggestion = ""
        
        if full_text and self.seo_keywords:
            keyword_density, density_rating, seo_suggestion = self.check_keyword_density(full_text)
        
        score = QualityScore(
            max_similarity=max_similarity,
            rating=rating,
            rating_en=rating_en,
            compared_count=len(self.history_fingerprints) - 1,
            keyword_density=keyword_density,
            density_rating=density_rating,
            seo_suggestion=seo_suggestion
        )
        
        logger.debug(f"质量检查: 重复率={max_similarity:.2%}, 评级={rating}, 对比数={score.compared_count}, SEO密度={keyword_density:.2%}")
        
        return score


class QualityReport:
    """质量报告生成器"""
    
    def __init__(self):
        self.records: List[Dict] = []
    
    def add_record(self, 
                   filename: str,
                   title: str,
                   max_similarity: float,
                   rating: str,
                   timestamp: datetime,
                   keyword_density: float = 0.0,
                   density_rating: str = "",
                   seo_suggestion: str = ""):
        """
        添加一条记录
        
        Args:
            filename: 文件名
            title: 标题
            max_similarity: 最大重复率
            rating: 评级
            timestamp: 生成时间
            keyword_density: 关键词密度
            density_rating: 密度评级
            seo_suggestion: SEO 建议
        """
        self.records.append({
            "文件名": filename,
            "标题": title,
            "最大重复率": f"{max_similarity:.2%}",
            "查重评级": rating,
            "关键词密度": f"{keyword_density:.2%}" if keyword_density > 0 else "-",
            "密度评级": density_rating if density_rating else "-",
            "SEO建议": seo_suggestion if seo_suggestion else "-",
            "生成时间": timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    def save_to_csv(self, output_path: str):
        """
        保存为 CSV 文件
        
        Args:
            output_path: 输出路径
        """
        import csv
        
        if not self.records:
            logger.warning("质量报告为空，跳过保存")
            return
        
        try:
            with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "文件名", "标题", "最大重复率", "查重评级", 
                    "关键词密度", "密度评级", "SEO建议", "生成时间"
                ])
                writer.writeheader()
                writer.writerows(self.records)
            
            logger.info(f"质量报告已保存: {output_path}, 共 {len(self.records)} 条记录")
        except Exception as e:
            logger.error(f"保存质量报告失败: {e}")
    
    def get_statistics(self) -> Dict[str, int]:
        """
        获取统计信息
        
        Returns:
            统计字典 {评级: 数量}
        """
        stats = {
            "查重_优质": 0, "查重_中等": 0, "查重_高重复": 0,
            "SEO_完美": 0, "SEO_不足": 0, "SEO_堆砌": 0
        }
        for record in self.records:
            # 查重统计
            rating = record.get("查重评级", "")
            if rating == "优质":
                stats["查重_优质"] += 1
            elif rating == "中等":
                stats["查重_中等"] += 1
            elif rating == "高重复":
                stats["查重_高重复"] += 1
            
            # SEO 统计
            density_rating = record.get("密度评级", "")
            if density_rating == "完美":
                stats["SEO_完美"] += 1
            elif density_rating == "不足":
                stats["SEO_不足"] += 1
            elif density_rating == "堆砌":
                stats["SEO_堆砌"] += 1
        
        return stats

