"""
历史查重配置对话框
允许用户配置全局查重参数
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from qfluentwidgets import (
    SwitchButton, SpinBox, LineEdit, PrimaryPushButton, PushButton,
    BodyLabel, StrongBodyLabel, CardWidget, InfoBar, InfoBarPosition,
    ComboBox, DoubleSpinBox, MessageBox
)
from loguru import logger

from ...config.settings import ProfileConfig


class DedupConfigDialog(QDialog):
    """历史查重配置对话框"""
    
    config_saved = pyqtSignal()  # 配置保存信号
    
    def __init__(self, config: ProfileConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self._init_ui()
        self._load_config()
    
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("历史查重配置")
        self.setMinimumWidth(500)
        self.setMinimumHeight(550)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 标题
        title_label = StrongBodyLabel("全局历史查重设置", self)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 说明文字
        desc_label = BodyLabel(
            "使用 SimHash 算法对生成的文章进行查重，确保长期唯一性。\n"
            "系统会自动保存每篇文章的指纹，生成时对比历史记录。",
            self
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #606060;")
        layout.addWidget(desc_label)
        
        # 启用开关卡片
        enable_card = CardWidget(self)
        enable_layout = QHBoxLayout(enable_card)
        enable_layout.setContentsMargins(16, 12, 16, 12)
        
        enable_label = BodyLabel("启用历史查重", self)
        self.enable_switch = SwitchButton(self)
        self.enable_switch.checkedChanged.connect(self._on_enable_changed)
        
        enable_layout.addWidget(enable_label)
        enable_layout.addStretch()
        enable_layout.addWidget(self.enable_switch)
        
        layout.addWidget(enable_card)
        
        # 配置卡片容器
        self.config_card = CardWidget(self)
        config_layout = QVBoxLayout(self.config_card)
        config_layout.setContentsMargins(16, 16, 16, 16)
        config_layout.setSpacing(16)
        
        # 1. 相似度阈值
        similarity_layout = QHBoxLayout()
        similarity_label = BodyLabel("相似度阈值:", self)
        similarity_label.setFixedWidth(120)
        
        self.similarity_spinbox = DoubleSpinBox(self)
        self.similarity_spinbox.setRange(0.50, 1.00)
        self.similarity_spinbox.setSingleStep(0.01)
        self.similarity_spinbox.setSuffix(" (90% = 距离≤6)")
        self.similarity_spinbox.setFixedWidth(200)
        
        similarity_tip = BodyLabel("推荐: 0.90 (90%)", self)
        similarity_tip.setStyleSheet("color: #909090; font-size: 12px;")
        
        similarity_layout.addWidget(similarity_label)
        similarity_layout.addWidget(self.similarity_spinbox)
        similarity_layout.addWidget(similarity_tip)
        similarity_layout.addStretch()
        
        config_layout.addLayout(similarity_layout)
        
        # 2. 最大重试次数
        retry_layout = QHBoxLayout()
        retry_label = BodyLabel("最大重试次数:", self)
        retry_label.setFixedWidth(120)
        
        self.retry_spinbox = SpinBox(self)
        self.retry_spinbox.setRange(1, 100)
        self.retry_spinbox.setSingleStep(1)
        self.retry_spinbox.setFixedWidth(200)
        
        retry_tip = BodyLabel("重复时重新抽取", self)
        retry_tip.setStyleSheet("color: #909090; font-size: 12px;")
        
        retry_layout.addWidget(retry_label)
        retry_layout.addWidget(self.retry_spinbox)
        retry_layout.addWidget(retry_tip)
        retry_layout.addStretch()
        
        config_layout.addLayout(retry_layout)
        
        # 3. 保留天数
        retention_layout = QHBoxLayout()
        retention_label = BodyLabel("指纹保留天数:", self)
        retention_label.setFixedWidth(120)
        
        self.retention_spinbox = SpinBox(self)
        self.retention_spinbox.setRange(1, 3650)
        self.retention_spinbox.setSingleStep(30)
        self.retention_spinbox.setSuffix(" 天")
        self.retention_spinbox.setFixedWidth(200)
        
        retention_tip = BodyLabel("默认半年 (180天)", self)
        retention_tip.setStyleSheet("color: #909090; font-size: 12px;")
        
        retention_layout.addWidget(retention_label)
        retention_layout.addWidget(self.retention_spinbox)
        retention_layout.addWidget(retention_tip)
        retention_layout.addStretch()
        
        config_layout.addLayout(retention_layout)
        
        # 4. 查重范围
        scope_layout = QHBoxLayout()
        scope_label = BodyLabel("查重范围:", self)
        scope_label.setFixedWidth(120)
        
        self.scope_combo = ComboBox(self)
        self.scope_combo.addItems(["仅当前项目", "全局所有项目"])
        self.scope_combo.setFixedWidth(200)
        
        scope_tip = BodyLabel("跨项目查重", self)
        scope_tip.setStyleSheet("color: #909090; font-size: 12px;")
        
        scope_layout.addWidget(scope_label)
        scope_layout.addWidget(self.scope_combo)
        scope_layout.addWidget(scope_tip)
        scope_layout.addStretch()
        
        config_layout.addLayout(scope_layout)
        
        # 5. 项目名称（仅当前项目时显示）
        project_layout = QHBoxLayout()
        self.project_label = BodyLabel("项目名称:", self)
        self.project_label.setFixedWidth(120)
        
        self.project_input = LineEdit(self)
        self.project_input.setPlaceholderText("输入项目名称（如：产品A）")
        self.project_input.setFixedWidth(200)
        
        project_tip = BodyLabel("用于区分不同项目", self)
        project_tip.setStyleSheet("color: #909090; font-size: 12px;")
        
        project_layout.addWidget(self.project_label)
        project_layout.addWidget(self.project_input)
        project_layout.addWidget(project_tip)
        project_layout.addStretch()
        
        config_layout.addLayout(project_layout)
        
        # 连接范围切换信号
        self.scope_combo.currentIndexChanged.connect(self._on_scope_changed)
        
        layout.addWidget(self.config_card)
        
        # 提示信息
        tip_card = CardWidget(self)
        tip_card.setStyleSheet("background-color: #FFF9E6; border: 1px solid #FFE58F;")
        tip_layout = QVBoxLayout(tip_card)
        tip_layout.setContentsMargins(12, 12, 12, 12)
        
        tip_title = BodyLabel("💡 温馨提示", self)
        tip_title.setStyleSheet("font-weight: bold; color: #D48806;")
        
        tip_content = BodyLabel(
            "• 海明距离映射：98%≤1, 95%≤3, 90%≤6, 85%≤10\n"
            "• 查重会轻微影响生成速度（每10万条 < 100ms）\n"
            "• 定期清理可提高查询效率（工具栏→管理）",
            self
        )
        tip_content.setStyleSheet("color: #8C6E1F; font-size: 12px;")
        tip_content.setWordWrap(True)
        
        tip_layout.addWidget(tip_title)
        tip_layout.addWidget(tip_content)
        
        layout.addWidget(tip_card)
        
        layout.addStretch()
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        # 管理指纹库按钮（左侧）
        self.manage_btn = PushButton("管理指纹库", self)
        self.manage_btn.clicked.connect(self._open_fingerprint_manager)
        button_layout.addWidget(self.manage_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = PrimaryPushButton("保存配置", self)
        self.save_btn.clicked.connect(self._save_config)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def _load_config(self):
        """加载配置到界面"""
        self.enable_switch.setChecked(self.config.dedup_enabled)
        self.similarity_spinbox.setValue(self.config.dedup_similarity_threshold)
        self.retry_spinbox.setValue(self.config.dedup_max_retries)
        self.retention_spinbox.setValue(self.config.dedup_retention_days)
        
        # 范围
        self.scope_combo.setCurrentIndex(1 if self.config.dedup_cross_project else 0)
        
        # 项目名称
        self.project_input.setText(self.config.dedup_current_project or "default")
        
        # 更新启用状态
        self._on_enable_changed(self.config.dedup_enabled)
        self._on_scope_changed(self.scope_combo.currentIndex())
        
        logger.debug("查重配置已加载到界面")
    
    def _on_enable_changed(self, checked: bool):
        """启用状态改变"""
        self.config_card.setEnabled(checked)
    
    def _on_scope_changed(self, index: int):
        """范围改变"""
        is_project_scope = (index == 0)  # 0=仅当前项目
        self.project_label.setVisible(is_project_scope)
        self.project_input.setVisible(is_project_scope)
    
    def _open_fingerprint_manager(self):
        """打开指纹库管理对话框"""
        from .fingerprint_manager_dialog import FingerprintManagerDialog
        
        dialog = FingerprintManagerDialog(self.config, self)
        dialog.exec()
    
    def _save_config(self):
        """保存配置"""
        try:
            # 更新配置
            self.config.dedup_enabled = self.enable_switch.isChecked()
            self.config.dedup_similarity_threshold = self.similarity_spinbox.value()
            self.config.dedup_max_retries = self.retry_spinbox.value()
            self.config.dedup_retention_days = self.retention_spinbox.value()
            self.config.dedup_cross_project = (self.scope_combo.currentIndex() == 1)
            self.config.dedup_current_project = self.project_input.text().strip() or "default"
            
            # 保存到文件
            self.config.save_config()
            
            # 显示成功提示
            InfoBar.success(
                title="保存成功",
                content=f"查重配置已保存 (阈值: {self.config.dedup_similarity_threshold*100:.0f}%)",
                duration=2000,
                position=InfoBarPosition.TOP,
                parent=self
            )
            
            # 发送信号
            self.config_saved.emit()
            
            logger.info(f"查重配置已保存: 启用={self.config.dedup_enabled}, 阈值={self.config.dedup_similarity_threshold}")
            
            # 关闭对话框
            self.accept()
            
        except Exception as e:
            logger.error(f"保存查重配置失败: {e}")
            MessageBox(
                "保存失败",
                f"无法保存配置: {str(e)}",
                self
            ).exec()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 测试配置
    from ...config.settings import ProfileConfig
    config = ProfileConfig()
    
    dialog = DedupConfigDialog(config)
    dialog.show()
    
    sys.exit(app.exec())

