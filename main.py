"""
SEO 智能内容工作台 - 主程序入口
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from qfluentwidgets import setTheme, Theme
from loguru import logger

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
 
from seo_workbench.config.settings import ProfileConfig
from seo_workbench.database.init_db import init_database
from seo_workbench.ui.main_window import MainWindow
from seo_workbench.ui.splash_screen import SplashScreen
from seo_workbench.utils.logger import setup_logger, setup_ui_logger
from seo_workbench.ui.styles import FluentStyle

def setup_high_dpi():
    """配置高分屏支持"""
    # 启用高 DPI 缩放
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = "1"
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )


def load_config() -> ProfileConfig:
    """加载配置文件"""
    config_path = "profile.json"
    if os.path.exists(config_path):
        try:
            config = ProfileConfig.load_from_file(config_path)
            logger.info(f"配置已加载: {config_path}")
            return config
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
    
    from seo_workbench.config.settings import create_default_config
    return create_default_config()


def main():
    """主函数"""
    setup_logger(log_level="INFO")
    setup_ui_logger()
    setup_high_dpi()
    
    app = QApplication(sys.argv)
    app.setApplicationName("SEO智能内容工作台")
    
    # 应用 Fluent Design 样式
    FluentStyle.apply_to_app(app)
    
    # 设置主题为自动（跟随系统）
    setTheme(Theme.AUTO)
    
    # 设置主题颜色为深天蓝
    from qfluentwidgets import setThemeColor
    from PyQt6.QtGui import QColor
    setThemeColor(QColor("#e5e4e3"))
    
    try:
        # 显示开屏动画（使用自定义背景图片）
        splash_image = r"E:\Case-5\seo_workbench\resources\splash.png"
        splash = SplashScreen(background_image=splash_image)
        splash.show()
        
        # 初始化数据库和配置
        db_manager = init_database("assets.db")
        config = load_config()
        
        # 创建主窗口（但先不显示）
        window = MainWindow(config, db_manager)
        
        # 当开屏动画完成时，显示主窗口
        def show_main_window():
            window.show()
            logger.info("应用启动完成")
        
        splash.finished.connect(show_main_window)
        
        return app.exec()
        
    except Exception as e:
        logger.critical(f"程序启动失败: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
