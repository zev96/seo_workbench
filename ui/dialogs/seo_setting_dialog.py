"""
SEO 核心词设置对话框
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    CardWidget, StrongBodyLabel, BodyLabel, PlainTextEdit,
    PrimaryPushButton, PushButton, FluentIcon as FIF,
    InfoBar, InfoBarPosition
)
from loguru import logger

from ...config.settings import ProfileConfig


class SEOSettingDialog(QDialog):
    """SEO 核心词设置对话框"""
    
    def __init__(self, config: ProfileConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self._init_ui()
        self._load_keywords()
        
    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle("关键词设置")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # === 标题区 ===
        title = StrongBodyLabel("🔍 关键词设置")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F1F1F;")
        layout.addWidget(title)
        
        # === 说明文字 ===
        desc = BodyLabel("请输入需要监控的 SEO 关键词，每行一个或用逗号分隔。\n系统将在生成文档时自动计算关键词密度并给出优化建议。")
        desc.setStyleSheet("color: #666666; font-size: 13px; line-height: 1.6;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # === 输入区卡片 ===
        input_card = CardWidget()
        input_card.setStyleSheet("""
            CardWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 16px;
                border: 1px solid #E5E5E5;
            }
        """)
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_layout.setSpacing(12)
        
        # 标签
        input_label = BodyLabel("关键词列表:")
        input_label.setStyleSheet("font-weight: 500; color: #1F1F1F;")
        input_layout.addWidget(input_label)
        
        # 大文本框
        self.keywords_input = PlainTextEdit()
        self.keywords_input.setPlaceholderText("示例：\n洗地机, 续航, 宠物\n或\n洗地机\n续航\n宠物")
        self.keywords_input.setMinimumHeight(250)
        self.keywords_input.setStyleSheet("""
            PlainTextEdit {
                background-color: #F8F8F8;
                border: 2px solid #E0E0E0;
                border-radius: 12px;
                padding: 15px;
                font-size: 14px;
                line-height: 1.8;
            }
            PlainTextEdit:focus {
                border-color: #4784d1;
                background-color: #FFFFFF;
            }
        """)
        input_layout.addWidget(self.keywords_input)
        
        # 提示文字
        hint = BodyLabel("💡 提示：关键词密度建议保持在 1%-3% 之间")
        hint.setStyleSheet("color: #999999; font-size: 12px;")
        input_layout.addWidget(hint)
        
        layout.addWidget(input_card)
        
        # === 底部按钮区 ===
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        # 取消按钮
        self.cancel_btn = PushButton("取消")
        self.cancel_btn.setFixedSize(100, 40)
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
            PushButton {
                background-color: #F5F5F5;
                border: none;
                border-radius: 8px;
                color: #666666;
                font-size: 14px;
            }
            PushButton:hover {
                background-color: #E8E8E8;
            }
        """)
        btn_layout.addWidget(self.cancel_btn)
        
        # 保存按钮
        self.save_btn = PrimaryPushButton(FIF.SAVE, "保存并生效")
        self.save_btn.setFixedSize(140, 40)
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setStyleSheet("""
            PrimaryPushButton {
                background-color: #4784d1;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 14px;
                font-weight: 500;
            }
            PrimaryPushButton:hover {
                background-color: #3a6fb8;
            }
            PrimaryPushButton:pressed {
                background-color: #2d5a99;
            }
        """)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_keywords(self):
        """加载现有关键词"""
        if self.config.target_keywords:
            # 每行一个关键词
            self.keywords_input.setPlainText("\n".join(self.config.target_keywords))
    
    def _on_save(self):
        """保存关键词"""
        text = self.keywords_input.toPlainText().strip()
        
        if not text:
            # 清空关键词
            self.config.target_keywords = []
            self.config.save_config()
            
            InfoBar.success(
                title='保存成功',
                content='SEO 关键词已清空',
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            logger.info("SEO 关键词已清空")
            self.accept()
            return
        
        # 解析关键词（支持逗号和换行）
        keywords = []
        for line in text.split('\n'):
            for kw in line.split(','):
                kw = kw.strip()
                if kw:
                    keywords.append(kw)
        
        if not keywords:
            InfoBar.warning(
                title='提示',
                content='请输入有效的关键词',
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        # 去重
        keywords = list(dict.fromkeys(keywords))
        
        # 保存到配置
        self.config.target_keywords = keywords
        self.config.save_config()
        
        InfoBar.success(
            title='保存成功',
            content=f'已保存 {len(keywords)} 个关键词',
            orient=Qt.Orientation.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
        logger.info(f"SEO 关键词已保存: {keywords}")
        self.accept()
    
    def get_keywords(self):
        """获取关键词列表"""
        return self.config.target_keywords

