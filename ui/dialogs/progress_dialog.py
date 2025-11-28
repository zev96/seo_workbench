"""
进度条对话框
显示文档生成进度
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
)
from PyQt6.QtCore import Qt


class ProgressDialog(QDialog):
    """进度条对话框"""
    
    def __init__(self, title: str = "处理中", parent=None):
        """
        初始化对话框
        
        Args:
            title: 对话框标题
            parent: 父窗口
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setModal(True)
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 状态标签
        self.status_label = QLabel("正在处理...")
        layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn)
    
    def set_progress(self, current: int, total: int):
        """
        设置进度
        
        Args:
            current: 当前进度
            total: 总数
        """
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.status_label.setText(f"正在处理: {current}/{total}")
    
    def set_status(self, status: str):
        """
        设置状态文本
        
        Args:
            status: 状态文本
        """
        self.status_label.setText(status)

