"""
混排策略面板
采用 Fluent Design 风格
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QEvent, QPropertyAnimation, QEasingCurve, QPoint, QRectF, pyqtProperty
from PyQt6.QtGui import QColor, QIcon, QMouseEvent, QCursor, QPainter, QPainterPath, QBrush, QPen
from qfluentwidgets import (
    CardWidget, StrongBodyLabel, BodyLabel, LineEdit, SpinBox, 
    SwitchButton, PrimaryPushButton, PushButton, ListWidget, TransparentToolButton,
    FluentIcon as FIF, InfoBar, MessageBox, PlainTextEdit, InfoBarPosition, IconWidget
)
from loguru import logger

from ...config.settings import ProfileConfig, ShufflingStrategy


class CardButton(QWidget):
    """自定义卡片按钮 - 图标和文字固定布局，使用组合模式，支持缓动动画"""
    
    clicked = pyqtSignal()
    
    def __init__(self, icon, text: str, parent=None):
        super().__init__(parent)
        self._icon = icon
        self._text = text
        self._is_pressed = False
        self._is_hovered = False
        
        # 动画属性
        self._bg_color = QColor("#F7F9FC")
        self._scale_factor = 1.0
        self._icon_base_size = 15 # 基础图标大小
        
        self._setup_ui()
        
        # 启用鼠标追踪
        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # 初始化动画
        self._init_animations()
    
    def _setup_ui(self):
        """设置内部布局"""
        # 创建水平布局
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(16, 0, 16, 0)
        self.layout.setSpacing(12)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # 添加图标
        self.icon_widget = IconWidget(self._icon, self)
        self.icon_widget.setFixedSize(self._icon_base_size, self._icon_base_size)
        self.layout.addWidget(self.icon_widget, 0, Qt.AlignmentFlag.AlignLeft)
        
        # 添加文字标签
        self.text_label = QLabel(self._text, self)
        self.text_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                color: #1F1F1F;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        self.layout.addWidget(self.text_label, 0, Qt.AlignmentFlag.AlignLeft)
        
        # 添加弹簧
        self.layout.addStretch(1)
        
        # 添加阴影效果
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(8)
        self.shadow_effect.setXOffset(0)
        self.shadow_effect.setYOffset(2)
        self.shadow_effect.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(self.shadow_effect)
        
        # 设置固定高度
        self.setFixedHeight(48)

    def _init_animations(self):
        """初始化动画"""
        # 缩放动画（弹弹效果）
        self.scale_anim = QPropertyAnimation(self, b"scale_factor")
        self.scale_anim.setDuration(400)  # 400ms
        self.scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)  # 回弹曲线
        
        # 背景色过渡动画
        self.bg_anim = QPropertyAnimation(self, b"bg_color")
        self.bg_anim.setDuration(200)
        
    # --- 属性定义 ---
    def get_scale_factor(self):
        return self._scale_factor
        
    def set_scale_factor(self, value):
        self._scale_factor = value
        # 对图标应用缩放
        scale = int(self._icon_base_size * value)
        self.icon_widget.setFixedSize(scale, scale)
        # 保持图标居中
        # self.icon_widget.move(16 - (scale - 15)//2, (48 - scale)//2)
        self.update()
        
    scale_factor = pyqtProperty(float, get_scale_factor, set_scale_factor)
    
    def get_bg_color(self):
        return self._bg_color
        
    def set_bg_color(self, color):
        self._bg_color = color
        self.update()
        
    bg_color = pyqtProperty(QColor, get_bg_color, set_bg_color)

    def paintEvent(self, event):
        """自定义绘制背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制背景
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 12, 12)
        
        painter.fillPath(path, self._bg_color)
        
        # 绘制边框
        border_color = QColor("rgba(229, 228, 227, 0.8)") if self._is_hovered else QColor("rgba(229, 228, 227, 0.2)")
        if self._is_hovered:
            border_color = QColor("#4784d1") # 悬浮时变蓝
            
        pen = QPen(border_color)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawPath(path)

    def enterEvent(self, event: QEvent):
        """鼠标进入：启动弹弹动画"""
        self._is_hovered = True
        
        # 启动缩放动画
        self.scale_anim.stop()
        self.scale_anim.setStartValue(1.0)
        self.scale_anim.setEndValue(1.2) # 放大1.2倍
        self.scale_anim.start()
        
        # 启动背景变白动画
        self.bg_anim.stop()
        self.bg_anim.setStartValue(self._bg_color)
        self.bg_anim.setEndValue(QColor("white"))
        self.bg_anim.start()
        
        # 阴影加深
        self.shadow_effect.setBlurRadius(18)
        self.shadow_effect.setYOffset(4)
        self.shadow_effect.setColor(QColor(0, 0, 0, 40))
        
        super().enterEvent(event)
    
    def leaveEvent(self, event: QEvent):
        """鼠标离开：恢复原状"""
        self._is_hovered = False
        self._is_pressed = False
        
        # 恢复缩放
        self.scale_anim.stop()
        self.scale_anim.setStartValue(self._scale_factor)
        self.scale_anim.setEndValue(1.0)
        self.scale_anim.start()
        
        # 恢复背景色
        self.bg_anim.stop()
        self.bg_anim.setStartValue(self._bg_color)
        self.bg_anim.setEndValue(QColor("#F7F9FC"))
        self.bg_anim.start()
        
        # 恢复阴影
        self.shadow_effect.setBlurRadius(8)
        self.shadow_effect.setYOffset(2)
        self.shadow_effect.setColor(QColor(0, 0, 0, 20))
        
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_pressed = True
            self._bg_color = QColor("rgba(248, 248, 250, 1)")
            self.shadow_effect.setBlurRadius(4)
            self.shadow_effect.setYOffset(1)
            self.update()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_pressed and self.rect().contains(event.pos()):
                self.clicked.emit()
            self._is_pressed = False
            if self._is_hovered:
                self.enterEvent(event) # 恢复悬浮状态
        super().mouseReleaseEvent(event)


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
        layout.setSpacing(12)
        
        # 1. 导入Excel
        self.import_excel_btn = CardButton(FIF.DOCUMENT, "导入Excel")
        self.import_excel_btn.clicked.connect(self.import_excel_clicked)
        layout.addWidget(self.import_excel_btn)
        
        # 2. 清空工作区
        self.clear_grid_btn = CardButton(FIF.DELETE, "清空工作区")
        self.clear_grid_btn.clicked.connect(self.clear_grid_clicked)
        layout.addWidget(self.clear_grid_btn)
        
        # 3. AI 标题生成
        self.ai_title_btn = CardButton(FIF.ROBOT, "AI 标题生成")
        self.ai_title_btn.clicked.connect(self.ai_title_clicked)
        layout.addWidget(self.ai_title_btn)
        
        # 4. 批量加粗
        self.bold_tool_btn = CardButton(FIF.FONT, "批量加粗")
        self.bold_tool_btn.clicked.connect(self.bold_tool_clicked)
        layout.addWidget(self.bold_tool_btn)
        
        # 5. SEO关键词设置
        self.seo_config_btn = CardButton(FIF.TAG, "SEO关键词设置")
        self.seo_config_btn.clicked.connect(self.seo_config_clicked)
        layout.addWidget(self.seo_config_btn)
        
        # 6. 随机组合设置
        self.config_strategy_btn = CardButton(FIF.LAYOUT, "随机组合设置")
        self.config_strategy_btn.clicked.connect(self.strategy_config_clicked)
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
