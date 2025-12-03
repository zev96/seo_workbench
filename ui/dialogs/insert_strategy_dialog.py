"""
插入策略配置对话框
配置品牌匹配和插入位置
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QGroupBox
)
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, LineEdit, SpinBox,
    ComboBox, PrimaryPushButton, CheckBox
)
from loguru import logger


class InsertStrategyDialog(MessageBoxBase):
    """插入策略配置对话框"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        
        # 默认配置
        self.config = {
            # 品牌匹配
            'own_brand_name': '希喂',  # 我方品牌名称
            'fallback_competitor_count': 2,  # 保底竞品数量
            
            # 插入位置
            'insert_mode': 'column',  # 插入模式: column/anchor
            'insert_column': 1,  # 在第N列后插入
            'insert_anchor_text': '参数对比',  # 锚点文本
        }
        
        # 加载已保存的配置
        saved_config = self.db_manager.get_config('insert_strategy')
        if saved_config:
            self.config.update(saved_config)
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        self.titleLabel = SubtitleLabel("插入策略配置")
        
        # 创建配置表单
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        
        # ==================== 品牌匹配配置 ====================
        brand_group = QGroupBox("品牌匹配与展示")
        brand_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        brand_layout = QGridLayout()
        brand_layout.setSpacing(15)
        
        row = 0
        
        # 我方品牌锁定
        brand_layout.addWidget(QLabel("我方品牌名称:"), row, 0)
        self.own_brand_input = LineEdit()
        self.own_brand_input.setText(self.config['own_brand_name'])
        self.own_brand_input.setPlaceholderText("如: 希喂")
        brand_layout.addWidget(self.own_brand_input, row, 1)
        row += 1
        
        # 说明文字
        hint_label = QLabel("(该品牌将永远出现在表格第一列，支持高亮显示)")
        hint_label.setStyleSheet("QLabel { color: #888; font-size: 11px; }")
        brand_layout.addWidget(hint_label, row, 0, 1, 2)
        row += 1
        
        # 保底机制
        brand_layout.addWidget(QLabel("保底竞品数量:"), row, 0)
        self.fallback_count_spin = SpinBox()
        self.fallback_count_spin.setRange(1, 10)
        self.fallback_count_spin.setValue(self.config['fallback_competitor_count'])
        brand_layout.addWidget(self.fallback_count_spin, row, 1)
        row += 1
        
        hint_label2 = QLabel("(如果文章未提及任何竞品，随机选取N个竞品)")
        hint_label2.setStyleSheet("QLabel { color: #888; font-size: 11px; }")
        brand_layout.addWidget(hint_label2, row, 0, 1, 2)
        row += 1
        
        brand_group.setLayout(brand_layout)
        main_layout.addWidget(brand_group)
        
        # ==================== 插入位置配置 ====================
        position_group = QGroupBox("插入位置")
        position_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        position_layout = QGridLayout()
        position_layout.setSpacing(15)
        
        row = 0
        
        # 插入模式选择
        position_layout.addWidget(QLabel("插入模式:"), row, 0)
        self.insert_mode_combo = ComboBox()
        self.insert_mode_combo.addItems([
            "按列插入 - 在第N列对应段落后",
            "智能锚点 - 检测到特定文本后"
        ])
        self.insert_mode_combo.setCurrentIndex(
            0 if self.config['insert_mode'] == 'column' else 1
        )
        self.insert_mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        position_layout.addWidget(self.insert_mode_combo, row, 1)
        row += 1
        
        # 按列插入配置
        position_layout.addWidget(QLabel("插入列号:"), row, 0)
        self.insert_column_spin = SpinBox()
        self.insert_column_spin.setRange(1, 10)
        self.insert_column_spin.setValue(self.config['insert_column'])
        position_layout.addWidget(self.insert_column_spin, row, 1)
        self.column_label = row
        row += 1
        
        # 智能锚点配置
        position_layout.addWidget(QLabel("锚点文本:"), row, 0)
        self.anchor_text_input = LineEdit()
        self.anchor_text_input.setText(self.config['insert_anchor_text'])
        self.anchor_text_input.setPlaceholderText("如: 参数对比")
        position_layout.addWidget(self.anchor_text_input, row, 1)
        self.anchor_label = row
        row += 1
        
        # 保存布局引用，用于切换显示
        self.position_layout = position_layout
        self._on_mode_changed(self.insert_mode_combo.currentIndex())
        
        position_group.setLayout(position_layout)
        main_layout.addWidget(position_group)
        
        # 将主布局添加到视图
        self.viewLayout.addLayout(main_layout)
        
        # 设置对话框属性
        self.widget.setMinimumWidth(550)
        
        # 添加按钮
        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")
        
        self.yesButton.clicked.connect(self._save_config)
    
    def _on_mode_changed(self, index):
        """插入模式改变"""
        # 根据选择显示/隐藏相应的配置项
        if index == 0:  # 按列插入
            # 显示列号，隐藏锚点
            self.position_layout.itemAtPosition(self.column_label, 0).widget().setVisible(True)
            self.insert_column_spin.setVisible(True)
            self.position_layout.itemAtPosition(self.anchor_label, 0).widget().setVisible(False)
            self.anchor_text_input.setVisible(False)
        else:  # 智能锚点
            # 隐藏列号，显示锚点
            self.position_layout.itemAtPosition(self.column_label, 0).widget().setVisible(False)
            self.insert_column_spin.setVisible(False)
            self.position_layout.itemAtPosition(self.anchor_label, 0).widget().setVisible(True)
            self.anchor_text_input.setVisible(True)
    
    def _save_config(self):
        """保存配置"""
        # 收集所有配置
        self.config['own_brand_name'] = self.own_brand_input.text().strip()
        self.config['fallback_competitor_count'] = self.fallback_count_spin.value()
        self.config['insert_mode'] = 'column' if self.insert_mode_combo.currentIndex() == 0 else 'anchor'
        self.config['insert_column'] = self.insert_column_spin.value()
        self.config['insert_anchor_text'] = self.anchor_text_input.text().strip()
        
        # 验证
        if not self.config['own_brand_name']:
            logger.warning("请输入我方品牌名称")
            return
        
        if self.config['insert_mode'] == 'anchor' and not self.config['insert_anchor_text']:
            logger.warning("请输入锚点文本")
            return
        
        # 保存到数据库
        if self.db_manager.save_config('insert_strategy', self.config):
            logger.info("插入策略配置保存成功")
            self.accept()
        else:
            logger.error("插入策略配置保存失败")

