"""
指纹数据库管理器
负责内容指纹的增删改查和查重逻辑
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy import and_, or_, func
from loguru import logger

from .models import ContentFingerprint
from .db_manager import DatabaseManager


class FingerprintManager:
    """内容指纹管理器"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """
        初始化指纹管理器
        
        Args:
            db_manager: 数据库管理器实例（可选）
        """
        self.db_manager = db_manager or DatabaseManager()
    
    def add_fingerprint(
        self,
        fingerprint: str,
        content_preview: str,
        full_content_hash: str,
        source_project: str = "",
        document_path: str = "",
        word_count: int = 0
    ) -> Optional[ContentFingerprint]:
        """
        添加新指纹
        
        Args:
            fingerprint: SimHash 指纹值（字符串格式）
            content_preview: 内容预览
            full_content_hash: 全文MD5哈希
            source_project: 来源项目
            document_path: 文档路径
            word_count: 字数统计
            
        Returns:
            创建的 ContentFingerprint 对象，失败返回 None
        """
        session = self.db_manager.get_session()
        try:
            # 创建指纹记录
            fp_record = ContentFingerprint(
                fingerprint=fingerprint,
                content_preview=content_preview[:200],  # 限制长度
                full_content_hash=full_content_hash,
                source_project=source_project,
                document_path=document_path,
                word_count=word_count,
                created_at=datetime.now()
            )
            
            session.add(fp_record)
            session.commit()
            session.refresh(fp_record)
            
            logger.info(f"指纹已添加: ID={fp_record.id}, 项目={source_project}, 字数={word_count}")
            return fp_record
            
        except Exception as e:
            session.rollback()
            logger.error(f"添加指纹失败: {e}")
            return None
        finally:
            session.close()
    
    def find_similar_fingerprints(
        self,
        target_fingerprint: int,
        max_distance: int = 6,
        source_project: str = None,
        limit: int = 10
    ) -> List[Tuple[ContentFingerprint, int]]:
        """
        查找相似的指纹（基于海明距离）
        
        Args:
            target_fingerprint: 目标指纹（64-bit整数）
            max_distance: 最大海明距离（默认6，对应90%相似度）
            source_project: 项目过滤（仅查同项目，None则查全部）
            limit: 返回结果数量限制
            
        Returns:
            [(ContentFingerprint, hamming_distance), ...] 按距离排序
        """
        session = self.db_manager.get_session()
        try:
            # 构建查询条件
            query = session.query(ContentFingerprint)
            
            # 项目过滤
            if source_project:
                query = query.filter(ContentFingerprint.source_project == source_project)
            
            # 获取候选指纹（注意：SQLite不支持位运算，需要在Python中计算）
            candidates = query.all()
            
            # 计算海明距离并筛选
            results = []
            for candidate in candidates:
                try:
                    candidate_fp = int(candidate.fingerprint)
                    distance = self._hamming_distance(target_fingerprint, candidate_fp)
                    
                    if distance <= max_distance:
                        results.append((candidate, distance))
                except ValueError:
                    logger.warning(f"无效的指纹格式: {candidate.fingerprint}")
                    continue
            
            # 按距离排序
            results.sort(key=lambda x: x[1])
            
            logger.debug(f"相似指纹查询: 找到 {len(results)} 条结果（距离≤{max_distance}）")
            return results[:limit]
            
        except Exception as e:
            logger.error(f"查找相似指纹失败: {e}")
            return []
        finally:
            session.close()
    
    def check_duplicate(
        self,
        target_fingerprint: int,
        full_content_hash: str,
        max_distance: int = 6,
        source_project: str = None
    ) -> Tuple[bool, Optional[ContentFingerprint], int]:
        """
        检查内容是否重复
        
        Args:
            target_fingerprint: 目标指纹（64-bit整数）
            full_content_hash: 全文MD5哈希（用于精确匹配）
            max_distance: 最大海明距离
            source_project: 项目过滤
            
        Returns:
            (is_duplicate, duplicate_record, hamming_distance)
            - is_duplicate: 是否重复
            - duplicate_record: 重复的记录（如果有）
            - hamming_distance: 海明距离（如果有相似记录）
        """
        session = self.db_manager.get_session()
        try:
            # 1. 精确匹配（MD5哈希）
            query = session.query(ContentFingerprint).filter(
                ContentFingerprint.full_content_hash == full_content_hash
            )
            if source_project:
                query = query.filter(ContentFingerprint.source_project == source_project)
            
            exact_match = query.first()
            if exact_match:
                logger.warning(f"发现完全相同的内容: ID={exact_match.id}, 项目={exact_match.source_project}")
                return (True, exact_match, 0)
            
            # 2. 模糊匹配（SimHash + 海明距离）
            similar = self.find_similar_fingerprints(
                target_fingerprint,
                max_distance=max_distance,
                source_project=source_project,
                limit=1
            )
            
            if similar:
                record, distance = similar[0]
                logger.warning(f"发现相似内容: ID={record.id}, 海明距离={distance}, 相似度≈{(64-distance)/64*100:.1f}%")
                return (True, record, distance)
            
            # 未发现重复
            return (False, None, -1)
            
        except Exception as e:
            logger.error(f"查重检查失败: {e}")
            return (False, None, -1)
        finally:
            session.close()
    
    def batch_check_duplicates(
        self,
        fingerprints: List[Tuple[int, str]],
        max_distance: int = 6,
        source_project: str = None
    ) -> List[Tuple[int, bool, Optional[ContentFingerprint]]]:
        """
        批量查重（提高效率）
        
        Args:
            fingerprints: [(simhash_int, md5_hash), ...] 指纹列表
            max_distance: 最大海明距离
            source_project: 项目过滤
            
        Returns:
            [(index, is_duplicate, duplicate_record), ...]
        """
        results = []
        
        for idx, (fp_int, md5_hash) in enumerate(fingerprints):
            is_dup, record, _ = self.check_duplicate(
                fp_int,
                md5_hash,
                max_distance=max_distance,
                source_project=source_project
            )
            results.append((idx, is_dup, record))
        
        duplicate_count = sum(1 for _, is_dup, _ in results if is_dup)
        logger.info(f"批量查重完成: 总数={len(fingerprints)}, 重复={duplicate_count}")
        
        return results
    
    def delete_fingerprint(self, fingerprint_id: int) -> bool:
        """
        删除指纹记录
        
        Args:
            fingerprint_id: 指纹ID
            
        Returns:
            是否删除成功
        """
        session = self.db_manager.get_session()
        try:
            record = session.query(ContentFingerprint).filter(
                ContentFingerprint.id == fingerprint_id
            ).first()
            
            if record:
                session.delete(record)
                session.commit()
                logger.info(f"指纹已删除: ID={fingerprint_id}")
                return True
            else:
                logger.warning(f"指纹不存在: ID={fingerprint_id}")
                return False
                
        except Exception as e:
            session.rollback()
            logger.error(f"删除指纹失败: {e}")
            return False
        finally:
            session.close()
    
    def clean_old_fingerprints(self, days: int = 180) -> int:
        """
        清理旧指纹（默认保留半年）
        
        Args:
            days: 保留天数
            
        Returns:
            删除的记录数
        """
        session = self.db_manager.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 查询旧记录
            old_records = session.query(ContentFingerprint).filter(
                ContentFingerprint.created_at < cutoff_date
            ).all()
            
            count = len(old_records)
            
            # 删除
            for record in old_records:
                session.delete(record)
            
            session.commit()
            logger.info(f"清理旧指纹: 删除 {count} 条记录（超过 {days} 天）")
            return count
            
        except Exception as e:
            session.rollback()
            logger.error(f"清理旧指纹失败: {e}")
            return 0
        finally:
            session.close()
    
    def get_statistics(self, source_project: str = None) -> dict:
        """
        获取指纹库统计信息
        
        Args:
            source_project: 项目过滤（可选）
            
        Returns:
            统计字典
        """
        session = self.db_manager.get_session()
        try:
            query = session.query(ContentFingerprint)
            
            if source_project:
                query = query.filter(ContentFingerprint.source_project == source_project)
            
            total_count = query.count()
            
            # 按项目分组统计
            project_stats = session.query(
                ContentFingerprint.source_project,
                func.count(ContentFingerprint.id)
            ).group_by(ContentFingerprint.source_project).all()
            
            # 最近7天新增
            week_ago = datetime.now() - timedelta(days=7)
            recent_count = query.filter(
                ContentFingerprint.created_at >= week_ago
            ).count()
            
            # 最早和最晚记录
            first_record = query.order_by(ContentFingerprint.created_at.asc()).first()
            last_record = query.order_by(ContentFingerprint.created_at.desc()).first()
            
            stats = {
                'total_count': total_count,
                'recent_week_count': recent_count,
                'project_breakdown': dict(project_stats),
                'first_created': first_record.created_at.isoformat() if first_record else None,
                'last_created': last_record.created_at.isoformat() if last_record else None
            }
            
            logger.info(f"指纹库统计: 总数={total_count}, 近7天={recent_count}")
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {'total_count': 0}
        finally:
            session.close()
    
    def clear_all_fingerprints(self, source_project: str = None) -> int:
        """
        清空指纹库（谨慎操作）
        
        Args:
            source_project: 项目过滤（仅清除指定项目，None则清除全部）
            
        Returns:
            删除的记录数
        """
        session = self.db_manager.get_session()
        try:
            query = session.query(ContentFingerprint)
            
            if source_project:
                query = query.filter(ContentFingerprint.source_project == source_project)
            
            count = query.count()
            query.delete()
            session.commit()
            
            project_msg = f"项目[{source_project}]" if source_project else "全部"
            logger.warning(f"清空指纹库: 删除 {count} 条记录（{project_msg}）")
            return count
            
        except Exception as e:
            session.rollback()
            logger.error(f"清空指纹库失败: {e}")
            return 0
        finally:
            session.close()
    
    @staticmethod
    def _hamming_distance(hash1: int, hash2: int) -> int:
        """
        计算两个64-bit整数的海明距离
        
        Args:
            hash1: 第一个哈希值
            hash2: 第二个哈希值
            
        Returns:
            海明距离（0-64）
        """
        # XOR运算得到不同的位
        xor_result = hash1 ^ hash2
        
        # 计算1的个数（Brian Kernighan算法）
        distance = 0
        while xor_result:
            distance += 1
            xor_result &= xor_result - 1
        
        return distance


if __name__ == "__main__":
    # 测试代码
    from ..utils.logger import setup_logger
    
    setup_logger()
    
    # 创建管理器
    manager = FingerprintManager()
    
    # 测试添加指纹
    fp1 = manager.add_fingerprint(
        fingerprint="12345678901234567890",
        content_preview="这是一段测试内容预览...",
        full_content_hash="abc123def456",
        source_project="test_project",
        document_path="output/test.docx",
        word_count=500
    )
    
    logger.info(f"添加指纹: {fp1}")
    
    # 测试统计
    stats = manager.get_statistics()
    logger.info(f"统计信息: {stats}")

