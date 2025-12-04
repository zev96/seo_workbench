"""
知乎监测设置对话框
配置Cookie、请求间隔、重试策略等
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QGroupBox, QFormLayout, QSpinBox, QTextEdit, QCheckBox, QFileDialog
)
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    PushButton, LineEdit, SpinBox, TextEdit, MessageBox,
    FluentIcon, ComboBox
)
from loguru import logger
from sqlalchemy.orm import Session
from ...database.models import ZhihuMonitorConfig


class ZhihuSettingsDialog(QDialog):
    """知乎监测设置对话框"""
    
    def __init__(self, db_session: Session, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self.setWindowTitle("知乎监测设置")
        self.resize(700, 600)
        
        self._init_ui()
        self._load_config()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Cookie配置区
        cookie_group = QGroupBox("🍪 Cookie 配置")
        cookie_layout = QVBoxLayout()
        
        cookie_info = QLabel(
            "💡 提示：设置Cookie可提高监测成功率，某些回答需要登录可见。\n"
            "获取方式：登录知乎后，打开开发者工具(F12) → Network → 刷新页面 → 选择任意请求 → Headers → Cookie"
        )
        cookie_info.setStyleSheet("color: #666; padding: 10px; background: #f5f5f5; border-radius: 5px;")
        cookie_info.setWordWrap(True)
        cookie_layout.addWidget(cookie_info)
        
        self.cookie_input = TextEdit()
        self.cookie_input.setPlaceholderText("粘贴完整的Cookie字符串...")
        self.cookie_input.setFixedHeight(120)
        cookie_layout.addWidget(self.cookie_input)
        
        cookie_group.setLayout(cookie_layout)
        layout.addWidget(cookie_group)
        
        # ChromeDriver 配置区
        driver_group = QGroupBox("🔧 ChromeDriver 配置")
        driver_layout = QVBoxLayout()
        
        driver_info = QLabel(
            "💡 提示：为降低知乎反爬检测，请手动配置本机 ChromeDriver 路径\n"
            "下载地址：https://googlechromelabs.github.io/chrome-for-testing/\n"
            "请确保 ChromeDriver 版本与本机 Chrome 浏览器版本一致"
        )
        driver_info.setStyleSheet("color: #666; padding: 10px; background: #f5f5f5; border-radius: 5px;")
        driver_info.setWordWrap(True)
        driver_layout.addWidget(driver_info)
        
        # ChromeDriver 路径选择
        path_layout = QHBoxLayout()
        self.chromedriver_path_input = LineEdit()
        self.chromedriver_path_input.setPlaceholderText("请选择 chromedriver.exe 文件路径...")
        path_layout.addWidget(self.chromedriver_path_input)
        
        self.browse_btn = PushButton("浏览...", self, FluentIcon.FOLDER)
        self.browse_btn.clicked.connect(self._browse_chromedriver)
        self.browse_btn.setFixedWidth(100)
        path_layout.addWidget(self.browse_btn)
        
        driver_layout.addLayout(path_layout)
        driver_group.setLayout(driver_layout)
        layout.addWidget(driver_group)
        
        # 防封策略配置
        anti_ban_group = QGroupBox("🛡️ 防封策略")
        anti_ban_layout = QFormLayout()
        anti_ban_layout.setSpacing(15)
        
        # 反检测强度选择
        self.anti_detect_combo = ComboBox()
        self.anti_detect_combo.addItems(["低（速度快）", "中（推荐）", "高（最稳定）"])
        self.anti_detect_combo.setCurrentIndex(1)  # 默认"中"
        self.anti_detect_combo.setToolTip(
            "低：最少停顿，8-12秒/任务\n"
            "中：适度模拟，15-30秒/任务（推荐）\n"
            "高：强模拟，40-60秒/任务（知乎风控重时使用）"
        )
        anti_ban_layout.addRow("反检测强度:", self.anti_detect_combo)
        
        # User-Agent
        self.user_agent_input = LineEdit()
        self.user_agent_input.setPlaceholderText("留空则使用内置User-Agent池")
        anti_ban_layout.addRow("User-Agent:", self.user_agent_input)
        
        # 请求间隔
        delay_layout = QHBoxLayout()
        self.delay_min_spin = SpinBox()
        self.delay_min_spin.setRange(1, 60)
        self.delay_min_spin.setValue(2)
        self.delay_min_spin.setSuffix(" 秒")
        
        self.delay_max_spin = SpinBox()
        self.delay_max_spin.setRange(1, 60)
        self.delay_max_spin.setValue(6)
        self.delay_max_spin.setSuffix(" 秒")
        
        delay_layout.addWidget(self.delay_min_spin)
        delay_layout.addWidget(QLabel(" 至 "))
        delay_layout.addWidget(self.delay_max_spin)
        delay_layout.addStretch()
        
        anti_ban_layout.addRow("请求间隔:", delay_layout)
        
        anti_ban_group.setLayout(anti_ban_layout)
        layout.addWidget(anti_ban_group)
        
        # 重试策略配置
        retry_group = QGroupBox("🔄 重试策略")
        retry_layout = QFormLayout()
        retry_layout.setSpacing(15)
        
        self.retry_count_spin = SpinBox()
        self.retry_count_spin.setRange(0, 10)
        self.retry_count_spin.setValue(3)
        self.retry_count_spin.setSuffix(" 次")
        retry_layout.addRow("失败重试次数:", self.retry_count_spin)
        
        self.retry_delay_spin = SpinBox()
        self.retry_delay_spin.setRange(60, 3600)
        self.retry_delay_spin.setValue(600)
        self.retry_delay_spin.setSuffix(" 秒")
        retry_layout.addRow("重试间隔:", self.retry_delay_spin)
        
        retry_group.setLayout(retry_layout)
        layout.addWidget(retry_group)
        
        # 温和模式配置（已被反检测强度替代，保留以兼容旧配置）
        gentle_group = QGroupBox("🛡️ 温和模式（已集成到反检测强度）")
        gentle_layout = QFormLayout()
        gentle_layout.setSpacing(15)
        
        self.gentle_mode_check = QCheckBox("启用温和模式（旧版，已不推荐）")
        self.gentle_mode_check.setToolTip(
            "温和模式下：\n"
            "• 请求间隔：8-15秒（更长）\n"
            "• 滚动次数：最多3次（更少）\n"
            "• 等待时间：3秒（更久）\n"
            "• 更安全，但数据可能不完整"
        )
        gentle_layout.addRow("", self.gentle_mode_check)
        
        gentle_group.setLayout(gentle_layout)
        layout.addWidget(gentle_group)
        
        # 说明文本
        note_label = QLabel(
            "⚠️ 注意事项：\n"
            "• 请求间隔建议设置在2-6秒，模拟正常浏览行为\n"
            "• 遇到403/429错误时会自动停止，避免IP被封\n"
            "• 重试间隔建议设置至少10分钟（600秒）"
        )
        note_label.setStyleSheet("color: #ff6b35; padding: 10px; background: #fff4f0; border-radius: 5px;")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)
        
        layout.addStretch()
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.reset_btn = PushButton("恢复默认", self, FluentIcon.SYNC)
        self.reset_btn.clicked.connect(self._reset_to_default)
        btn_layout.addWidget(self.reset_btn)
        
        self.save_btn = PushButton("保存设置", self, FluentIcon.SAVE)
        self.save_btn.clicked.connect(self._save_config)
        btn_layout.addWidget(self.save_btn)
        
        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def _browse_chromedriver(self):
        """浏览选择 ChromeDriver 文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 ChromeDriver 可执行文件",
            "",
            "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        
        if file_path:
            self.chromedriver_path_input.setText(file_path)
            logger.info(f"已选择 ChromeDriver: {file_path}")
        
    def _load_config(self):
        """加载配置"""
        try:
            config = self.db_session.query(ZhihuMonitorConfig).first()
            
            if config:
                self.cookie_input.setPlainText(config.cookie or "")
                self.user_agent_input.setText(config.user_agent or "")
                self.delay_min_spin.setValue(config.request_delay_min)
                self.delay_max_spin.setValue(config.request_delay_max)
                self.retry_count_spin.setValue(config.retry_count)
                self.retry_delay_spin.setValue(config.retry_delay)
                self.gentle_mode_check.setChecked(getattr(config, 'gentle_mode', 0) == 1)
                
                # 加载新字段
                self.chromedriver_path_input.setText(getattr(config, 'chromedriver_path', '') or '')
                
                # 加载反检测强度
                anti_detect_level = getattr(config, 'anti_detect_level', 'medium') or 'medium'
                level_map = {'low': 0, 'medium': 1, 'high': 2}
                self.anti_detect_combo.setCurrentIndex(level_map.get(anti_detect_level, 1))
                
                logger.info("已加载知乎监测配置")
            else:
                logger.info("未找到配置，使用默认值")
                
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
    
    def _save_config(self):
        """保存配置"""
        try:
            # 验证输入
            if self.delay_min_spin.value() > self.delay_max_spin.value():
                MessageBox("提示", "最小间隔不能大于最大间隔", self).exec()
                return
            
            # 验证 ChromeDriver 路径
            chromedriver_path = self.chromedriver_path_input.text().strip()
            if chromedriver_path:
                import os
                if not os.path.exists(chromedriver_path):
                    MessageBox("警告", f"ChromeDriver 路径不存在:\n{chromedriver_path}\n\n请确认路径是否正确", self).exec()
                    # 不阻止保存，仅警告
            
            config = self.db_session.query(ZhihuMonitorConfig).first()
            
            if not config:
                config = ZhihuMonitorConfig()
                self.db_session.add(config)
            
            # 更新配置
            config.cookie = self.cookie_input.toPlainText().strip() or None
            config.user_agent = self.user_agent_input.text().strip() or None
            config.request_delay_min = self.delay_min_spin.value()
            config.request_delay_max = self.delay_max_spin.value()
            config.retry_count = self.retry_count_spin.value()
            config.retry_delay = self.retry_delay_spin.value()
            config.gentle_mode = 1 if self.gentle_mode_check.isChecked() else 0
            
            # 保存新字段
            config.chromedriver_path = chromedriver_path or None
            
            # 保存反检测强度
            level_map = {0: 'low', 1: 'medium', 2: 'high'}
            config.anti_detect_level = level_map.get(self.anti_detect_combo.currentIndex(), 'medium')
            
            self.db_session.commit()
            
            logger.success("知乎监测配置已保存")
            MessageBox("成功", "配置已保存", self).exec()
            
            self.accept()
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"保存配置失败: {e}")
            MessageBox("错误", f"保存失败: {e}", self).exec()
    
    def _reset_to_default(self):
        """恢复默认设置"""
        reply = MessageBox(
            "确认重置",
            "确定要恢复默认设置吗？",
            self
        )
        
        if reply.exec():
            self.cookie_input.clear()
            self.user_agent_input.clear()
            self.delay_min_spin.setValue(2)
            self.delay_max_spin.setValue(6)
            self.retry_count_spin.setValue(3)
            self.retry_delay_spin.setValue(600)
            
            logger.info("已恢复默认设置")
    
    def get_config_dict(self) -> dict:
        """
        获取当前配置字典
        
        Returns:
            配置字典
        """
        try:
            config = self.db_session.query(ZhihuMonitorConfig).first()
            
            if config:
                return {
                    'cookie': config.cookie,
                    'user_agent': config.user_agent,
                    'delay_min': config.request_delay_min,
                    'delay_max': config.request_delay_max,
                    'retry_count': config.retry_count,
                    'retry_delay': config.retry_delay,
                    'gentle_mode': getattr(config, 'gentle_mode', 0),
                    'chromedriver_path': getattr(config, 'chromedriver_path', None),
                    'anti_detect_level': getattr(config, 'anti_detect_level', 'medium')
                }
            else:
                # 返回默认配置
                return {
                    'cookie': None,
                    'user_agent': None,
                    'delay_min': 2,
                    'delay_max': 6,
                    'retry_count': 3,
                    'retry_delay': 600,
                    'gentle_mode': 0,
                    'chromedriver_path': None,
                    'anti_detect_level': 'medium'
                }
                
        except Exception as e:
            logger.error(f"获取配置失败: {e}")
            return {}

