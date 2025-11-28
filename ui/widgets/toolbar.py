"""
顶部工具栏
采用 Fluent Design 风格
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from qfluentwidgets import (
    PrimaryPushButton, PushButton, LineEdit, ComboBox, 
    SpinBox, CardWidget, FluentIcon as FIF, Action, CommandBar
)
from loguru import logger

from ...config.settings import ProfileConfig


class Toolbar(CardWidget):
    """工具栏组件 (Fluent 风格)"""
    
    # 信号定义
    generate_clicked = pyqtSignal(str)  # 生成模式
    
    def __init__(self, config: ProfileConfig):
        super().__init__()
        self.config = config
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        # 设置固定高度
        self.setFixedHeight(60)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(12)
        
        # 生成控制区
        layout.addWidget(QLabel("模式:"))
        self.mode_combo = ComboBox()
        self.mode_combo.addItems(["按行生成", "随机混排"])
        self.mode_combo.setFixedWidth(120)
        layout.addWidget(self.mode_combo)
        
        layout.addWidget(QLabel("数量:"))
        self.count_spin = SpinBox()
        self.count_spin.setRange(1, 1000)
        self.count_spin.setValue(50)
        self.count_spin.setEnabled(False)
        self.count_spin.setMinimumWidth(100)
        layout.addWidget(self.count_spin)
        
        self.mode_combo.currentIndexChanged.connect(
            lambda idx: self.count_spin.setEnabled(idx == 1)
        )
        
        # 主要操作按钮 (Primary)
        self.generate_btn = PrimaryPushButton(FIF.PLAY, "开始生成 Word")
        self.generate_btn.clicked.connect(self._on_generate_clicked)
        layout.addWidget(self.generate_btn)
        
        layout.addStretch()
    
    def _on_generate_clicked(self):
        """生成按钮点击"""
        mode = "row" if self.mode_combo.currentIndex() == 0 else "shuffle"
        self.generate_clicked.emit(mode)
