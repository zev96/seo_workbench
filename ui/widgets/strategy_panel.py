"""
混排策略面板
采用 Fluent Design 风格
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from qfluentwidgets import (
    CardWidget, StrongBodyLabel, BodyLabel, LineEdit, SpinBox, 
    SwitchButton, PrimaryPushButton, PushButton, ListWidget, TransparentToolButton,
    FluentIcon as FIF, InfoBar, MessageBox, PlainTextEdit, InfoBarPosition
)
from loguru import logger

from ...config.settings import ProfileConfig, ShufflingStrategy


class StrategyPanel(QWidget):
    """策略面板组件 (Fluent 风格)"""
    
    # 信号定义
    import_excel_clicked = pyqtSignal()  # 导入 Excel
    clear_grid_clicked = pyqtSignal()    # 清空工作区
    bold_tool_clicked = pyqtSignal()     # 批量加粗设置
    ai_title_clicked = pyqtSignal()      # AI 标题生成
    strategy_config_clicked = pyqtSignal()  # 混排策略配置
    seo_config_clicked = pyqtSignal()    # SEO 核心词配置
    
    def __init__(self, config: ProfileConfig):
        super().__init__()
        self.config = config
        self.validator = None
        self._init_ui()
        self._update_strategy_count()

    def set_validator(self, func):
        """设置验证回调函数"""
        self.validator = func
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 统一按钮样式
        button_style = """
            PushButton {
                background-color: rgba(248, 248, 250, 0.85);
                border-radius: 5px;
                padding: 10px 12px;
                font-size: 13px;
                font-weight: 500;
                text-align: center;
            }
            PushButton:hover {
                background-color: #f8f8f8;       /* 悬停背景变亮 */
                border-bottom: 1px solid #e5e4e3; /* 加厚底部边框，模拟立体阴影 */
                margin-bottom: 1px;              /* 微调位置，产生按压感 */
                font-weight: bold;
            }
        """
        
        ai_button_style = """
            PrimaryPushButton {
                background-color: rgba(248, 248, 250, 0.85);
                border-radius: 5px;
                padding: 10px 12px;
                font-size: 13px;
                font-weight: 500;
                text-align: center;
            }
            PrimaryPushButton:hover {
                background-color: #f8f8f8;       /* 悬停背景变亮 */
                border-bottom: 1px solid #e5e4e3; /* 【核心】加厚底部边框，模拟立体阴影 */
                margin-bottom: 1px;              /* 微调位置，产生按压感 */
                font-weight: bold;
            }
            PrimaryPushButton:pressed {
                background-color: #f8f8f8;
            }
        """
        
        # 1. 导入Excel
        self.import_excel_btn = PushButton("导入Excel")
        self.import_excel_btn.clicked.connect(self.import_excel_clicked)
        self.import_excel_btn.setFixedHeight(42)
        self.import_excel_btn.setStyleSheet(button_style)
        layout.addWidget(self.import_excel_btn)
        
        # 2. 清空工作区
        self.clear_grid_btn = PushButton("清空工作区")
        self.clear_grid_btn.clicked.connect(self.clear_grid_clicked)
        self.clear_grid_btn.setFixedHeight(42)
        self.clear_grid_btn.setStyleSheet(button_style)
        layout.addWidget(self.clear_grid_btn)
        
        # 3. AI 标题生成
        self.ai_title_btn = PrimaryPushButton("AI 标题生成")
        self.ai_title_btn.clicked.connect(self.ai_title_clicked)
        self.ai_title_btn.setFixedHeight(42)
        self.ai_title_btn.setStyleSheet(ai_button_style)
        layout.addWidget(self.ai_title_btn)
        
        # 4. 批量加粗
        self.bold_tool_btn = PushButton("批量加粗")
        self.bold_tool_btn.clicked.connect(self.bold_tool_clicked)
        self.bold_tool_btn.setFixedHeight(42)
        self.bold_tool_btn.setStyleSheet(button_style)
        layout.addWidget(self.bold_tool_btn)
        
        # 5. 配置 SEO 核心词
        self.seo_config_btn = PushButton("SEO关键词设置")
        self.seo_config_btn.clicked.connect(self.seo_config_clicked)
        self.seo_config_btn.setFixedHeight(42)
        self.seo_config_btn.setStyleSheet(button_style)
        layout.addWidget(self.seo_config_btn)
        
        # 6. 配置高级混排策略
        self.config_strategy_btn = PushButton("随机组合设置")
        self.config_strategy_btn.clicked.connect(self.strategy_config_clicked)
        self.config_strategy_btn.setFixedHeight(42)
        self.config_strategy_btn.setStyleSheet(button_style)
        layout.addWidget(self.config_strategy_btn)
        
        # 弹性空间
        layout.addStretch()
    
    def _update_strategy_count(self):
        """更新策略数量（极简模式无需显示）"""
        count = len(self.config.shuffling_strategies)
        logger.debug(f"策略数量更新: {count}")
    
    def update_seo_status(self):
        """更新 SEO 关键词状态（极简模式无需显示）"""
        keyword_count = len(self.config.target_keywords)
        logger.debug(f"SEO 关键词数量更新: {keyword_count}")
