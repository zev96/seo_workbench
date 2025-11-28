"""
批量加粗设置对话框
配置生成文档时的自动加粗规则
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    PlainTextEdit, PrimaryPushButton, PushButton, 
    StrongBodyLabel, BodyLabel
)
from ...config.settings import ProfileConfig


class BoldToolDialog(QDialog):
    """批量加粗设置对话框"""
    
    def __init__(self, config: ProfileConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self._init_ui()
        
    def _init_ui(self):
        self.setWindowTitle("批量加粗设置")
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        layout.addWidget(StrongBodyLabel("加粗关键词配置"))
        layout.addWidget(BodyLabel("在生成文档时，以下关键词将自动加粗（每行一个）："))
        
        self.keywords_edit = PlainTextEdit()
        self.keywords_edit.setPlaceholderText("输入关键词...")
        if self.config.bold_keywords:
            self.keywords_edit.setPlainText('\n'.join(self.config.bold_keywords))
        layout.addWidget(self.keywords_edit)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = PushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.save_btn = PrimaryPushButton("保存配置")
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
        
    def _on_save(self):
        """保存配置"""
        text = self.keywords_edit.toPlainText().strip()
        keywords = [line.strip() for line in text.split('\n') if line.strip()]
        
        self.config.bold_keywords = keywords
        self.config.save_config()
        
        self.accept()
