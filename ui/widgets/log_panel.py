"""
日志面板
底部可折叠面板，显示运行日志
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QComboBox, QLabel
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QTextCursor
from loguru import logger

from ...utils.logger import get_log_capture


class LogPanel(QWidget):
    """日志面板组件"""
    
    def __init__(self):
        """初始化日志面板"""
        super().__init__()
        self.log_capture = get_log_capture()
        self._init_ui()
        self._start_update_timer()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 顶部控制栏
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("运行日志"))
        
        # 日志级别过滤
        control_layout.addWidget(QLabel("级别:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["全部", "INFO", "WARNING", "ERROR"])
        self.level_combo.currentTextChanged.connect(self._on_level_changed)
        control_layout.addWidget(self.level_combo)
        
        control_layout.addStretch()
        
        # 清空按钮
        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self._on_clear)
        control_layout.addWidget(self.clear_btn)
        
        # 折叠按钮
        self.toggle_btn = QPushButton("折叠")
        self.toggle_btn.clicked.connect(self._on_toggle)
        control_layout.addWidget(self.toggle_btn)
        
        layout.addLayout(control_layout)
        
        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        self.is_collapsed = False
    
    def _start_update_timer(self):
        """启动更新定时器"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_logs)
        self.update_timer.start(1000)  # 每秒更新一次
    
    def _update_logs(self):
        """更新日志显示"""
        level = self.level_combo.currentText()
        
        if level == "全部":
            logs = self.log_capture.get_logs()
        else:
            logs = self.log_capture.get_logs(level)
        
        # 只显示最后 100 条
        logs = logs[-100:]
        
        # 更新文本框
        current_text = '\n'.join(logs)
        if current_text != self.log_text.toPlainText():
            self.log_text.setPlainText(current_text)
            # 滚动到底部
            self.log_text.moveCursor(QTextCursor.MoveOperation.End)
    
    def _on_level_changed(self, level: str):
        """日志级别改变"""
        self._update_logs()
    
    def _on_clear(self):
        """清空日志"""
        self.log_capture.clear()
        self.log_text.clear()
        logger.info("日志已清空")
    
    def _on_toggle(self):
        """折叠/展开"""
        if self.is_collapsed:
            self.log_text.show()
            self.toggle_btn.setText("折叠")
            self.is_collapsed = False
        else:
            self.log_text.hide()
            self.toggle_btn.setText("展开")
            self.is_collapsed = True

