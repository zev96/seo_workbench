"""
开屏动画（Splash Screen）
在应用启动时显示加载界面
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QLinearGradient
from qfluentwidgets import ProgressBar, BodyLabel, TitleLabel
import random


class SplashScreen(QWidget):
    """应用启动开屏动画"""
    
    finished = pyqtSignal()  # 加载完成信号
    
    def __init__(self):
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
        
        self._init_ui()
        self._start_animation()
    
    def _init_ui(self):
        """初始化UI"""
        # 窗口设置
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(500, 350)
        
        # 居中显示
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # 背景样式（渐变色）
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
        
        layout.addStretch(1)
        
        # Logo/标题（带emoji图标）
        title_label = TitleLabel("🚀 SEO 智能内容工作台")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            TitleLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                background: transparent;
                letter-spacing: 2px;
            }
        """)
        layout.addWidget(title_label)
        
        # 版本信息
        version_label = BodyLabel("v1.0.0 Beta")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("""
            BodyLabel {
                color: rgba(255, 255, 255, 180);
                font-size: 14px;
                background: transparent;
            }
        """)
        layout.addWidget(version_label)
        
        layout.addSpacing(30)
        
        # 加载提示文本
        self.status_label = BodyLabel("正在启动应用...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            BodyLabel {
                color: white;
                font-size: 13px;
                background: transparent;
            }
        """)
        layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = ProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            ProgressBar {
                background-color: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
            }
            ProgressBar::chunk {
                background-color: white;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 百分比显示
        self.percent_label = BodyLabel("0%")
        self.percent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.percent_label.setStyleSheet("""
            BodyLabel {
                color: rgba(255, 255, 255, 200);
                font-size: 12px;
                background: transparent;
            }
        """)
        layout.addWidget(self.percent_label)
        
        layout.addStretch(1)
        
        # 底部版权信息
        footer_label = BodyLabel("Powered by PyQt6 & Fluent Design")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setStyleSheet("""
            BodyLabel {
                color: rgba(255, 255, 255, 150);
                font-size: 11px;
                background: transparent;
            }
        """)
        layout.addWidget(footer_label)
    
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
        """绘制背景（添加阴影效果）"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制阴影
        shadow_rect = self.rect().adjusted(5, 5, -5, -5)
        painter.setBrush(QColor(0, 0, 0, 50))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(shadow_rect, 15, 15)
        
        super().paintEvent(event)

