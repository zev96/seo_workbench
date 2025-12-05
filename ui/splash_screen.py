"""
开屏动画（Splash Screen）
在应用启动时显示加载界面
支持自定义背景图片和布局位置
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QRect
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QLinearGradient
from qfluentwidgets import ProgressBar, BodyLabel, TitleLabel
import random
import os


class SplashScreen(QWidget):
    """应用启动开屏动画（支持自定义背景图片）"""
    
    finished = pyqtSignal()  # 加载完成信号
    
    def __init__(self, background_image: str = None):
        """
        初始化开屏动画
        
        Args:
            background_image: 背景图片路径（可选）
                            如果为None，使用默认渐变背景
                            如果指定路径，使用自定义图片
        """
        super().__init__()
        self.progress_value = 0
        self.loading_steps = [
            "正在初始化系统...",
            "正在加载配置文件...",
            "正在连接数据库...",
            "正在加载UI组件...",
            "正在初始化监控服务...",
            "准备就绪，即将启动..."
        ]
        self.current_step = 0
        self.background_image = background_image
        self.background_pixmap = None
        
        # 加载背景图片
        if background_image and os.path.exists(background_image):
            self.background_pixmap = QPixmap(background_image)
        
        self._init_ui()
        self._start_animation()
    
    def _init_ui(self):
        """初始化UI（使用绝对定位，方便调整位置）"""
        # 窗口设置
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 根据背景图片调整窗口大小
        if self.background_pixmap:
            self.setFixedSize(self.background_pixmap.size())
        else:
            self.setFixedSize(500, 350)
        
        # 居中显示
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        
        # 如果没有自定义背景图片，使用渐变背景
        if not self.background_pixmap:
            self.setStyleSheet("""
                SplashScreen {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, 
                        stop:1 #764ba2
                    );
                    border-radius: 15px;
                }
            """)
        
        # ==================== 可调整的位置参数 ====================
        window_width = self.width()
        window_height = self.height()
        
        # 标题位置（距离顶部的比例）
        title_top_ratio = 0.25  # 25%的位置
        title_top = int(window_height * title_top_ratio)
        
        # 版本信息位置
        version_top = title_top + 50
        
        # 状态文本位置（距离底部的固定距离）
        status_bottom = window_height - 120
        
        # 进度条位置
        progress_bottom = window_height - 80
        
        # 百分比位置
        percent_bottom = window_height - 55
        
        # 版权信息位置
        footer_bottom = window_height - 25
        # ========================================================
        
        # Logo/标题（绝对定位）
        self.title_label = TitleLabel(" ", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setGeometry(0, title_top, window_width, 40)
        self.title_label.setStyleSheet("""
            TitleLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                background: transparent;
                letter-spacing: 2px;
            }
        """)
        
        # 版本信息
        self.version_label = BodyLabel("v1.0.0 Beta", self)
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setGeometry(0, version_top, window_width, 30)
        self.version_label.setStyleSheet("""
            BodyLabel {
                color: rgba(0, 0, 0, 180);
                font-size: 10px;
                background: transparent;
            }
        """)
        
        # 加载提示文本
        self.status_label = BodyLabel("正在启动应用...", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setGeometry(0, status_bottom, window_width, 30)
        self.status_label.setStyleSheet("""
            BodyLabel {
                color: white;
                font-size: 13px;
                background: transparent;
            }
        """)
        
        # 进度条
        progress_width = int(window_width * 0.7)  # 宽度为窗口的70%
        progress_left = (window_width - progress_width) // 2
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setGeometry(progress_left, progress_bottom, progress_width, 8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            ProgressBar {
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 4px;
            }
            ProgressBar::chunk {
                background-color: white;
                border-radius: 4px;
            }
        """)
        
        # 百分比显示
        self.percent_label = BodyLabel("0%", self)
        self.percent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.percent_label.setGeometry(0, percent_bottom, window_width, 25)
        self.percent_label.setStyleSheet("""
            BodyLabel {
                color: rgba(255, 255, 255, 200);
                font-size: 10px;
                background: transparent;
            }
        """)
        
        # 底部版权信息
        self.footer_label = BodyLabel(" ", self)
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer_label.setGeometry(0, footer_bottom, window_width, 20)
        self.footer_label.setStyleSheet("""
            BodyLabel {
                color: rgba(255, 255, 255, 150);
                font-size: 5px;
                background: transparent;
            }
        """)
    
    def _start_animation(self):
        """启动加载动画"""
        # 使用定时器模拟加载进度
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_progress)
        self.timer.start(50)  # 每50毫秒更新一次
    
    def _update_progress(self):
        """更新进度"""
        # 渐进式增加进度
        if self.progress_value < 100:
            # 模拟真实加载速度（前期快，后期慢）
            if self.progress_value < 30:
                increment = random.randint(3, 6)
            elif self.progress_value < 70:
                increment = random.randint(2, 4)
            else:
                increment = random.randint(1, 2)
            
            self.progress_value = min(100, self.progress_value + increment)
            self.progress_bar.setValue(self.progress_value)
            self.percent_label.setText(f"{self.progress_value}%")
            
            # 更新加载提示文本
            step_index = int(self.progress_value / (100 / len(self.loading_steps)))
            if step_index < len(self.loading_steps) and step_index != self.current_step:
                self.current_step = step_index
                self.status_label.setText(self.loading_steps[step_index])
        else:
            # 加载完成
            self.timer.stop()
            QTimer.singleShot(300, self._fade_out)
    
    def _fade_out(self):
        """淡出动画"""
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.finished.connect(self._on_animation_finished)
        self.animation.start()
    
    def _on_animation_finished(self):
        """动画完成"""
        self.finished.emit()
        self.close()
    
    def paintEvent(self, event):
        """绘制背景（支持自定义图片或渐变色）"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.background_pixmap:
            # 绘制背景图片
            painter.drawPixmap(self.rect(), self.background_pixmap)
        else:
            # 如果没有图片，绘制渐变背景（由样式表处理）
            # 绘制阴影效果
            shadow_rect = self.rect().adjusted(5, 5, -5, -5)
            painter.setBrush(QColor(0, 0, 0, 50))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(shadow_rect, 15, 15)
        
        super().paintEvent(event)

