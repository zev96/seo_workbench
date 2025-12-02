"""
进度条对话框
显示文档生成进度 - Fluent Design 风格
"""

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, BodyLabel, ProgressBar,
    PrimaryPushButton, TransparentPushButton, FluentIcon as FIF,
    IndeterminateProgressBar
)
from loguru import logger


class ProgressDialog(MessageBoxBase):
    """进度对话框 - Fluent Design 风格"""
    
    # 信号：用户点击取消
    cancelled = pyqtSignal()
    
    def __init__(self, title: str = "正在生成文档", total: int = 0, parent=None):
        """
        初始化对话框
        
        Args:
            title: 对话框标题
            total: 总任务数量
            parent: 父窗口
        """
        super().__init__(parent)
        self.total = total
        self.current = 0
        self._is_cancelled = False
        
        self.titleLabel = SubtitleLabel(title, self)
        self.statusLabel = BodyLabel("准备开始...", self)
        
        # 进度条（使用确定进度条或不确定进度条）
        if total > 0:
            self.progressBar = ProgressBar(self)
            self.progressBar.setRange(0, 100)
            self.progressBar.setValue(0)
        else:
            # 不确定进度条（用于未知总数的情况）
            self.progressBar = IndeterminateProgressBar(self)
            self.progressBar.start()
        
        # 详细信息标签
        self.detailLabel = BodyLabel("", self)
        self.detailLabel.setWordWrap(True)
        self.detailLabel.setStyleSheet("color: #7A7A7A; font-size: 12px;")
        
        # 按钮
        self.cancelButton = TransparentPushButton("取消", self)
        self.cancelButton.clicked.connect(self._on_cancel)
        
        self._init_ui()
        
        # 设置对话框属性
        self.setMinimumWidth(480)
        self.setMinimumHeight(320)
        self.widget.setFixedSize(480, 320)
    
        
        # 禁止关闭按钮
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        
        logger.debug(f"进度对话框初始化完成: total={total}")
    
    def _init_ui(self):
        """初始化 UI"""
        # 添加组件到主布局
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(8)
        self.viewLayout.addWidget(self.statusLabel)
        self.viewLayout.addSpacing(12)
        self.viewLayout.addWidget(self.progressBar)
        self.viewLayout.addSpacing(8)
        self.viewLayout.addWidget(self.detailLabel)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancelButton)
        self.viewLayout.addLayout(button_layout)
    
    def set_progress(self, current: int, total: int = None):
        """
        设置进度
        
        Args:
            current: 当前进度
            total: 总数（可选，如果不提供则使用初始化时的值）
        """
        self.current = current
        if total is not None:
            self.total = total
        
        if self.total > 0:
            percentage = int((current / self.total) * 100)
            if isinstance(self.progressBar, ProgressBar):
                self.progressBar.setValue(percentage)
            
            self.statusLabel.setText(f"正在处理: {current}/{self.total} ({percentage}%)")
        else:
            self.statusLabel.setText(f"正在处理: {current} 项")
        
        logger.debug(f"进度更新: {current}/{self.total}")
    
    def set_status(self, status: str):
        """
        设置状态文本
        
        Args:
            status: 状态文本
        """
        self.statusLabel.setText(status)
        logger.debug(f"状态更新: {status}")
    
    def set_detail(self, detail: str):
        """
        设置详细信息
        
        Args:
            detail: 详细信息文本
        """
        self.detailLabel.setText(detail)
    
    def complete(self, success: bool = True, message: str = ""):
        """
        完成进度
        
        Args:
            success: 是否成功
            message: 完成消息
        """
        if isinstance(self.progressBar, ProgressBar):
            self.progressBar.setValue(100)
        elif isinstance(self.progressBar, IndeterminateProgressBar):
            self.progressBar.stop()
        
        if success:
            self.statusLabel.setText(message or "处理完成！")
            self.titleLabel.setText("✓ 生成完成")
        else:
            self.statusLabel.setText(message or "处理失败")
            self.titleLabel.setText("✗ 生成失败")
        
        # 更改按钮文本
        self.cancelButton.setText("关闭")
        self.cancelButton.disconnect()
        self.cancelButton.clicked.connect(self.accept)
        
        logger.info(f"进度完成: success={success}, message={message}")
    
    def _on_cancel(self):
        """处理取消操作"""
        self._is_cancelled = True
        self.statusLabel.setText("正在取消...")
        self.cancelButton.setEnabled(False)
        self.cancelled.emit()
        logger.info("用户请求取消")
    
    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        return self._is_cancelled

