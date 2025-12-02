"""
文档生成工作线程
用于在后台执行文档生成任务，避免阻塞UI
"""

from PyQt6.QtCore import QThread, pyqtSignal
from loguru import logger
from typing import List


class GenerationWorker(QThread):
    """文档生成工作线程"""
    
    # 信号定义
    progress_updated = pyqtSignal(int, int, str)  # (current, total, detail)
    status_changed = pyqtSignal(str)  # status message
    generation_complete = pyqtSignal(bool, str, int)  # (success, message, count)
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(
        self,
        grid_data: List[List[str]],
        save_dir: str,
        mode: str,
        count: int,
        config,
        generate_func,
        parent=None
    ):
        """
        初始化工作线程
        
        Args:
            grid_data: 网格数据
            save_dir: 保存目录
            mode: 生成模式 ("row" 或 "shuffle")
            count: 生成数量
            config: 配置对象
            generate_func: 生成函数引用
            parent: 父对象
        """
        super().__init__(parent)
        self.grid_data = grid_data
        self.save_dir = save_dir
        self.mode = mode
        self.count = count
        self.config = config
        self.generate_func = generate_func
        self._is_cancelled = False
        
        logger.debug(f"GenerationWorker初始化: mode={mode}, count={count}")
    
    def run(self):
        """执行生成任务"""
        try:
            self.status_changed.emit("正在初始化...")
            logger.info(f"开始生成文档: mode={self.mode}, count={self.count}")
            
            # 调用生成函数（带进度回调）
            generated_count = self.generate_func(
                grid_data=self.grid_data,
                save_dir=self.save_dir,
                mode=self.mode,
                count=self.count,
                progress_callback=self._on_progress
            )
            
            if self._is_cancelled:
                self.generation_complete.emit(False, "生成已取消", 0)
                logger.info("生成任务被取消")
            else:
                self.generation_complete.emit(
                    True,
                    f"成功生成 {generated_count} 个文档",
                    generated_count
                )
                logger.info(f"生成任务完成: {generated_count} 个文档")
        
        except Exception as e:
            error_msg = f"生成失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
            self.generation_complete.emit(False, error_msg, 0)
    
    def _on_progress(self, current: int, total: int, detail: str = ""):
        """
        进度回调函数
        
        Args:
            current: 当前进度
            total: 总数
            detail: 详细信息
        """
        # 检查是否取消
        if self._is_cancelled:
            raise InterruptedError("用户取消操作")
        
        # 发送进度信号
        self.progress_updated.emit(current, total, detail)
    
    def cancel(self):
        """取消生成任务"""
        self._is_cancelled = True
        logger.info("请求取消生成任务")

