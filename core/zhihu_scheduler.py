"""
知乎监测定时任务调度器
支持每日定时自动检测
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict
from loguru import logger
from PyQt6.QtCore import QThread, pyqtSignal

from sqlalchemy.orm import Session
from ..database.models import ZhihuMonitorTask, ZhihuBrand, ZhihuMonitorHistory
from .zhihu_monitor_worker import ZhihuMonitorWorker


class ZhihuScheduler(QThread):
    """知乎监测定时调度器"""
    
    # 信号定义
    schedule_triggered = pyqtSignal(str)  # 调度触发（时间字符串）
    task_started = pyqtSignal(int)  # 任务开始（任务数）
    task_progress = pyqtSignal(int, int, str)  # 任务进度
    task_finished = pyqtSignal(dict)  # 任务完成（统计信息）
    
    def __init__(self, db_session: Session):
        """
        初始化调度器
        
        Args:
            db_session: 数据库会话
        """
        super().__init__()
        self.db_session = db_session
        self._stop_flag = False
        self._check_interval = 60  # 检查间隔（秒）
        self.worker = None
        
    def run(self):
        """线程主函数"""
        logger.info("知乎监测调度器已启动")
        
        while not self._stop_flag:
            try:
                # 检查是否有需要执行的定时任务
                current_time = datetime.now()
                current_hour = current_time.hour
                current_minute = current_time.minute
                
                # 查询启用了定时任务的监控
                tasks = self.db_session.query(ZhihuMonitorTask).filter(
                    ZhihuMonitorTask.schedule_enabled == 1,
                    ZhihuMonitorTask.schedule_time.isnot(None)
                ).all()
                
                for task in tasks:
                    schedule_time = task.schedule_time  # 格式: "HH:MM"
                    
                    if not schedule_time or ':' not in schedule_time:
                        continue
                    
                    try:
                        target_hour, target_minute = map(int, schedule_time.split(':'))
                        
                        # 检查是否到达执行时间（允许1分钟误差）
                        if (current_hour == target_hour and 
                            abs(current_minute - target_minute) <= 1):
                            
                            # 检查今天是否已执行过
                            last_check = task.last_check_at
                            if last_check:
                                last_check_date = last_check.date()
                                today = current_time.date()
                                
                                if last_check_date == today:
                                    # 今天已执行过，跳过
                                    continue
                            
                            # 触发定时任务
                            self._execute_scheduled_tasks()
                            
                            # 执行后休眠，避免重复触发
                            time.sleep(120)
                            break
                        
                    except Exception as e:
                        logger.error(f"解析定时时间失败: {schedule_time} - {e}")
                
                # 休眠一段时间后再检查
                time.sleep(self._check_interval)
                
            except Exception as e:
                logger.error(f"调度器异常: {e}")
                time.sleep(self._check_interval)
        
        logger.info("知乎监测调度器已停止")
    
    def stop(self):
        """停止调度器"""
        self._stop_flag = True
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
    
    def _execute_scheduled_tasks(self):
        """执行定时任务"""
        try:
            # 获取所有启用定时的任务
            tasks = self.db_session.query(ZhihuMonitorTask).filter(
                ZhihuMonitorTask.schedule_enabled == 1
            ).all()
            
            if not tasks:
                logger.info("没有启用定时的任务")
                return
            
            logger.info(f"开始执行定时任务，共 {len(tasks)} 个")
            self.schedule_triggered.emit(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.task_started.emit(len(tasks))
            
            # 获取配置
            from ..database.models import ZhihuMonitorConfig
            config_obj = self.db_session.query(ZhihuMonitorConfig).first()
            
            config = {
                'cookie': config_obj.cookie if config_obj else None,
                'user_agent': config_obj.user_agent if config_obj else None,
                'delay_min': config_obj.request_delay_min if config_obj else 2,
                'delay_max': config_obj.request_delay_max if config_obj else 6,
            }
            
            # 获取品牌关键词
            brands = self.db_session.query(ZhihuBrand).all()
            brand_keywords = [brand.name for brand in brands]
            
            # 准备任务数据
            task_list = []
            for task in tasks:
                task_list.append({
                    'id': task.id,
                    'url': task.question_url,
                    'title': task.question_title,
                    'target_brand': task.target_brand,
                    'check_range': task.check_range
                })
            
            # 创建工作线程
            self.worker = ZhihuMonitorWorker(task_list, config, brand_keywords)
            self.worker.progress_updated.connect(self._on_progress)
            self.worker.task_completed.connect(self._on_task_completed)
            self.worker.task_failed.connect(self._on_task_failed)
            self.worker.all_completed.connect(self._on_all_completed)
            
            # 启动
            self.worker.start()
            self.worker.wait()  # 等待完成
            
        except Exception as e:
            logger.error(f"执行定时任务失败: {e}")
    
    def _on_progress(self, current: int, total: int, message: str):
        """进度更新"""
        self.task_progress.emit(current, total, message)
    
    def _on_task_completed(self, task_id: int, result: dict):
        """任务完成回调"""
        try:
            task = self.db_session.query(ZhihuMonitorTask).filter(
                ZhihuMonitorTask.id == task_id
            ).first()
            
            if task:
                import json
                task.question_title = result.get('question_title')
                task.total_views = result.get('total_views', 0)
                task.total_followers = result.get('total_followers', 0)
                task.set_result_list(result.get('found_ranks', []))
                task.status = result.get('status', 'success')
                task.last_check_at = datetime.now()
                
                # 保存历史记录
                history = ZhihuMonitorHistory(
                    task_id=task_id,
                    check_result=json.dumps(result.get('found_ranks', [])),
                    total_views=result.get('total_views', 0),
                    total_followers=result.get('total_followers', 0)
                )
                self.db_session.add(history)
                
                self.db_session.commit()
                
                logger.success(f"定时任务 {task_id} 完成")
                
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"保存定时任务结果失败: {e}")
    
    def _on_task_failed(self, task_id: int, error: str):
        """任务失败回调"""
        try:
            task = self.db_session.query(ZhihuMonitorTask).filter(
                ZhihuMonitorTask.id == task_id
            ).first()
            
            if task:
                task.status = 'failed'
                task.last_check_at = datetime.now()
                self.db_session.commit()
                
                logger.error(f"定时任务 {task_id} 失败: {error}")
                
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"更新任务状态失败: {e}")
    
    def _on_all_completed(self):
        """所有任务完成"""
        # 统计结果
        stats = {
            'completed_at': datetime.now().isoformat(),
            'success_count': 0,
            'failed_count': 0
        }
        
        try:
            tasks = self.db_session.query(ZhihuMonitorTask).filter(
                ZhihuMonitorTask.schedule_enabled == 1
            ).all()
            
            for task in tasks:
                if task.status == 'success':
                    stats['success_count'] += 1
                elif task.status == 'failed':
                    stats['failed_count'] += 1
        except:
            pass
        
        self.task_finished.emit(stats)
        logger.success(f"定时任务全部完成: 成功 {stats['success_count']}, 失败 {stats['failed_count']}")

