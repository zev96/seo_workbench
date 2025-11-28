"""
API 设置对话框
配置 AI API 相关参数
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QSpinBox, QPushButton, QMessageBox,
    QFormLayout
)
from loguru import logger

from ...config.settings import ProfileConfig


class APISettingsDialog(QDialog):
    """API 设置对话框"""
    
    def __init__(self, config: ProfileConfig, parent=None):
        """
        初始化对话框
        
        Args:
            config: 配置对象
            parent: 父窗口
        """
        super().__init__(parent)
        self.config = config
        self._init_ui()
        self._load_config()
    
    def _init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("API 设置")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # 表单布局
        form_layout = QFormLayout()
        
        # Base URL
        self.base_url_input = QLineEdit()
        form_layout.addRow("Base URL:", self.base_url_input)
        
        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("API Key:", self.api_key_input)
        
        # Model
        self.model_input = QLineEdit()
        form_layout.addRow("模型:", self.model_input)
        
        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 120)
        self.timeout_spin.setSuffix(" 秒")
        form_layout.addRow("超时:", self.timeout_spin)
        
        # Max Retries
        self.retries_spin = QSpinBox()
        self.retries_spin.setRange(0, 10)
        form_layout.addRow("最大重试:", self.retries_spin)
        
        layout.addLayout(form_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self._on_test)
        btn_layout.addWidget(self.test_btn)
        
        btn_layout.addStretch()
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_config(self):
        """加载配置"""
        api_config = self.config.api_config
        self.base_url_input.setText(api_config.base_url)
        self.api_key_input.setText(api_config.api_key)
        self.model_input.setText(api_config.model)
        self.timeout_spin.setValue(api_config.timeout)
        self.retries_spin.setValue(api_config.max_retries)
    
    def _on_test(self):
        """测试连接"""
        try:
            from ...ai.api_client import AIClient
            from ...config.settings import APIConfig
            
            # 创建临时配置
            temp_config = APIConfig(
                base_url=self.base_url_input.text(),
                api_key=self.api_key_input.text(),
                model=self.model_input.text(),
                timeout=self.timeout_spin.value(),
                max_retries=self.retries_spin.value()
            )
            
            # 测试连接
            client = AIClient(temp_config)
            if client.test_connection():
                QMessageBox.information(self, "成功", "API 连接测试成功！")
            else:
                QMessageBox.warning(self, "失败", "API 连接测试失败，请检查配置")
                
        except Exception as e:
            logger.error(f"测试连接失败: {e}")
            QMessageBox.critical(self, "错误", f"测试失败：{str(e)}")
    
    def accept(self):
        """保存配置"""
        try:
            self.config.api_config.base_url = self.base_url_input.text()
            self.config.api_config.api_key = self.api_key_input.text()
            self.config.api_config.model = self.model_input.text()
            self.config.api_config.timeout = self.timeout_spin.value()
            self.config.api_config.max_retries = self.retries_spin.value()
            
            logger.info("API 配置已更新")
            super().accept()
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存失败：{str(e)}")

