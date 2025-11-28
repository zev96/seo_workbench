"""
Fluent Design 样式表
Windows 11 风格 + Glassmorphism
"""
from pathlib import Path
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication
from loguru import logger


class FluentStyle:
    """Fluent Design 样式管理器"""
    
    # 配色方案 - Technoloze 磨砂玻璃风格
    THEME_COLOR = "#e5e4e3"  # 深天蓝
    BACKGROUND_COLOR = "rgba(248, 248, 250, 0.85)"  # 高透明度磨砂白
    CARD_COLOR = "rgba(255, 255, 255, 0.95)"  # 纯白卡片（微透明）
    CARD_SELECTED = "#FFFFFF"  # 选中项纯白背景
    TEXT_PRIMARY = "#1F1F1F"  # 主要文字
    TEXT_SECONDARY = "#7A7A7A"  # 次要文字（中灰）
    TEXT_SELECTED = "#000000"  # 选中项文字（深黑）
    BORDER_COLOR = "#E5E5E5"  # 边框颜色
    SHADOW_COLOR = "rgba(0, 0, 0, 0.08)"  # 阴影颜色
    
    @staticmethod
    def load_font():
        """
        加载 OPPO Sans 字体
        如果失败则回退到 Microsoft YaHei
        
        Returns:
            QFont: 加载的字体对象
        """
        font_name = "Microsoft YaHei"  # 默认字体
        
        try:
            # 尝试加载 OPPO Sans 字体文件
            font_dir = Path(__file__).parent.parent.parent / "resources" / "fonts"
            
            # 尝试多个可能的文件名
            possible_names = [
                "OPPO Sans 4.0.ttf",
                "OPPOSans-Regular.ttf",
                "OPPO Sans.ttf"
            ]
            
            oppo_font_path = None
            for name in possible_names:
                path = font_dir / name
                if path.exists():
                    oppo_font_path = path
                    break
            
            if oppo_font_path and oppo_font_path.exists():
                font_id = QFontDatabase.addApplicationFont(str(oppo_font_path))
                if font_id != -1:
                    font_families = QFontDatabase.applicationFontFamilies(font_id)
                    if font_families:
                        font_name = font_families[0]
                        logger.info(f"成功加载字体: {font_name}")
                    else:
                        logger.warning("OPPO Sans 字体加载失败，使用默认字体")
                else:
                    logger.warning("OPPO Sans 字体 ID 无效，使用默认字体")
            else:
                logger.info(f"OPPO Sans 字体文件不存在: {oppo_font_path}，使用默认字体")
        except Exception as e:
            logger.error(f"加载字体时出错: {e}，使用默认字体")
        
        # 创建字体对象
        font = QFont(font_name)
        font.setPointSize(10)
        
        return font
    
    @staticmethod
    def get_global_stylesheet() -> str:
        """
        获取全局样式表 - Technoloze 磨砂玻璃风格
        
        Returns:
            str: QSS 样式表
        """
        return f"""
        /* ========== 全局样式 ========== */
        * {{
            font-family: "OPPO Sans", "Microsoft YaHei", "Segoe UI", sans-serif;
        }}
        
        /* 主窗口背景 */
        QWidget {{
            background-color: {FluentStyle.BACKGROUND_COLOR};
            color: {FluentStyle.TEXT_PRIMARY};
        }}
        
        /* ========== 卡片容器 ========== */
        CardWidget {{
            background-color: {FluentStyle.CARD_COLOR};
            border-radius: 16px;
            border: 1px solid {FluentStyle.BORDER_COLOR};
            padding: 20px;
        }}
        
        /* ========== 按钮样式 ========== */
        PrimaryPushButton {{
            background-color: {FluentStyle.THEME_COLOR};
            border: none;
            border-radius: 10px;
            color: white;
            padding: 12px 20px;
            font-weight: 500;
            font-size: 14px;
        }}
        
        PrimaryPushButton:hover {{
            background-color: #3a6fb8;
        }}
        
        PrimaryPushButton:pressed {{
            background-color: #2d5a99;
        }}
        
        PushButton {{
            background-color: {FluentStyle.CARD_COLOR};
            border: 1px solid {FluentStyle.BORDER_COLOR};
            border-radius: 10px;
            color: {FluentStyle.TEXT_PRIMARY};
            padding: 10px 18px;
            font-size: 13px;
        }}
        
        PushButton:hover {{
            background-color: #F8F8F8;
            border-color: {FluentStyle.THEME_COLOR};
        }}
        
        /* ========== 输入框样式 ========== */
        LineEdit, PlainTextEdit, TextEdit {{
            background-color: rgba(248, 248, 248, 0.9);
            border: 2px solid {FluentStyle.BORDER_COLOR};
            border-radius: 12px;
            padding: 12px;
            color: {FluentStyle.TEXT_PRIMARY};
            font-size: 13px;
        }}
        
        LineEdit:focus, PlainTextEdit:focus, TextEdit:focus {{
            border-color: {FluentStyle.THEME_COLOR};
            background-color: #FFFFFF;
        }}
        
        /* ========== 表格样式 ========== */
        TableWidget {{
            background-color: {FluentStyle.CARD_COLOR};
            border: 1px solid {FluentStyle.BORDER_COLOR};
            border-radius: 16px;
            gridline-color: {FluentStyle.BORDER_COLOR};
        }}
        
        TableWidget::item {{
            padding: 8px;
        }}
        
        /* ========== 列表样式 ========== */
        ListWidget {{
            background-color: {FluentStyle.CARD_COLOR};
            border: 1px solid {FluentStyle.BORDER_COLOR};
            border-radius: 12px;
        }}
        
        /* ========== 下拉框样式 ========== */
        ComboBox {{
            background-color: {FluentStyle.CARD_COLOR};
            border: 1px solid {FluentStyle.BORDER_COLOR};
            border-radius: 10px;
            padding: 8px 12px;
        }}
        
        /* ========== 滚动条样式 ========== */
        QScrollBar:vertical {{
            background-color: transparent;
            width: 10px;
            border-radius: 5px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: rgba(0, 0, 0, 0.15);
            border-radius: 5px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: rgba(0, 0, 0, 0.25);
        }}
        
        QScrollBar:horizontal {{
            background-color: transparent;
            height: 10px;
            border-radius: 5px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: rgba(0, 0, 0, 0.15);
            border-radius: 5px;
            min-width: 30px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: rgba(0, 0, 0, 0.25);
        }}
        """
    
    @staticmethod
    def apply_to_app(app: QApplication):
        """
        应用样式到应用程序
        
        Args:
            app: QApplication 实例
        """
        # 加载字体
        font = FluentStyle.load_font()
        app.setFont(font)
        
        # 应用样式表
        # app.setStyleSheet(FluentStyle.get_global_stylesheet())
        
        logger.info("Fluent Design 样式已应用")

