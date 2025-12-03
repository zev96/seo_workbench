"""
表格样式设置对话框
配置生成图片的样式
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QColorDialog, QPushButton,
    QGridLayout, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, ComboBox, SpinBox,
    PushButton, PrimaryPushButton, ColorDialog, LineEdit
)
from loguru import logger


class TableStyleDialog(MessageBoxBase):
    """表格样式设置对话框"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        
        # 默认配置
        self.config = {
            'preset': 'business_blue',  # 预设风格
            'header_bg_color': '#4472C4',  # 表头背景色
            'header_text_color': '#FFFFFF',  # 表头文字颜色
            'own_brand_bg_color': '#FFF2CC',  # 我方品牌背景色
            'border_width': 1.5,  # 边框粗细
            'image_width': 15,  # 图片宽度（厘米）
            'dpi': 300,  # 分辨率
            'font_name': 'Microsoft YaHei',  # 字体
            'font_size': 10  # 字号
        }
        
        # 加载已保存的配置
        saved_config = self.db_manager.get_config('table_style')
        if saved_config:
            self.config.update(saved_config)
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        self.titleLabel = SubtitleLabel("表格样式设置")
        
        # 创建配置表单
        form_layout = QGridLayout()
        form_layout.setSpacing(15)
        
        row = 0
        
        # 1. 预设风格
        form_layout.addWidget(QLabel("预设风格:"), row, 0)
        self.preset_combo = ComboBox()
        self.preset_combo.addItems([
            "商务蓝 (Business Blue)",
            "清新绿 (Fresh Green)",
            "强对比黄 (High Contrast Yellow)"
        ])
        self.preset_combo.setCurrentIndex(
            ['business_blue', 'fresh_green', 'high_contrast'].index(self.config['preset'])
            if self.config['preset'] in ['business_blue', 'fresh_green', 'high_contrast']
            else 0
        )
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        form_layout.addWidget(self.preset_combo, row, 1)
        row += 1
        
        # 2. 表头背景色
        form_layout.addWidget(QLabel("表头背景色:"), row, 0)
        self.header_bg_btn = PushButton("选择颜色")
        self.header_bg_btn.clicked.connect(lambda: self._pick_color('header_bg_color'))
        self.header_bg_label = QLabel()
        self.header_bg_label.setFixedSize(50, 25)
        self._update_color_label(self.header_bg_label, self.config['header_bg_color'])
        color_layout = QHBoxLayout()
        color_layout.addWidget(self.header_bg_btn)
        color_layout.addWidget(self.header_bg_label)
        color_layout.addStretch()
        form_layout.addLayout(color_layout, row, 1)
        row += 1
        
        # 3. 表头文字颜色
        form_layout.addWidget(QLabel("表头文字颜色:"), row, 0)
        self.header_text_btn = PushButton("选择颜色")
        self.header_text_btn.clicked.connect(lambda: self._pick_color('header_text_color'))
        self.header_text_label = QLabel()
        self.header_text_label.setFixedSize(50, 25)
        self._update_color_label(self.header_text_label, self.config['header_text_color'])
        color_layout2 = QHBoxLayout()
        color_layout2.addWidget(self.header_text_btn)
        color_layout2.addWidget(self.header_text_label)
        color_layout2.addStretch()
        form_layout.addLayout(color_layout2, row, 1)
        row += 1
        
        # 4. 我方品牌背景色
        form_layout.addWidget(QLabel("我方品牌背景色:"), row, 0)
        self.own_brand_btn = PushButton("选择颜色")
        self.own_brand_btn.clicked.connect(lambda: self._pick_color('own_brand_bg_color'))
        self.own_brand_label = QLabel()
        self.own_brand_label.setFixedSize(50, 25)
        self._update_color_label(self.own_brand_label, self.config['own_brand_bg_color'])
        color_layout3 = QHBoxLayout()
        color_layout3.addWidget(self.own_brand_btn)
        color_layout3.addWidget(self.own_brand_label)
        color_layout3.addStretch()
        form_layout.addLayout(color_layout3, row, 1)
        row += 1
        
        # 5. 边框粗细
        form_layout.addWidget(QLabel("边框粗细:"), row, 0)
        self.border_width_spin = SpinBox()
        self.border_width_spin.setRange(1, 5)
        self.border_width_spin.setValue(int(self.config['border_width']))
        form_layout.addWidget(self.border_width_spin, row, 1)
        row += 1
        
        # 6. 图片宽度（厘米）
        form_layout.addWidget(QLabel("图片宽度 (cm):"), row, 0)
        self.image_width_spin = SpinBox()
        self.image_width_spin.setRange(10, 20)
        self.image_width_spin.setValue(self.config['image_width'])
        form_layout.addWidget(self.image_width_spin, row, 1)
        row += 1
        
        # 7. 分辨率 DPI
        form_layout.addWidget(QLabel("分辨率 (DPI):"), row, 0)
        self.dpi_combo = ComboBox()
        self.dpi_combo.addItems(["150", "200", "300", "400"])
        self.dpi_combo.setCurrentText(str(self.config['dpi']))
        form_layout.addWidget(self.dpi_combo, row, 1)
        row += 1
        
        # 8. 字体
        form_layout.addWidget(QLabel("字体:"), row, 0)
        self.font_combo = ComboBox()
        self.font_combo.addItems([
            "Microsoft YaHei",
            "SimHei",
            "SimSun",
            "Arial"
        ])
        self.font_combo.setCurrentText(self.config['font_name'])
        form_layout.addWidget(self.font_combo, row, 1)
        row += 1
        
        # 9. 字号
        form_layout.addWidget(QLabel("字号:"), row, 0)
        self.font_size_spin = SpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setValue(self.config['font_size'])
        form_layout.addWidget(self.font_size_spin, row, 1)
        row += 1
        
        # 将表单添加到视图
        self.viewLayout.addLayout(form_layout)
        
        # 设置对话框属性
        self.widget.setMinimumWidth(500)
        
        # 添加按钮
        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")
        
        self.yesButton.clicked.connect(self._save_config)
    
    def _update_color_label(self, label, color_hex):
        """更新颜色标签"""
        label.setStyleSheet(f"""
            QLabel {{
                background-color: {color_hex};
                border: 1px solid #ccc;
                border-radius: 3px;
            }}
        """)
    
    def _pick_color(self, config_key):
        """选择颜色"""
        current_color = QColor(self.config[config_key])
        color = QColorDialog.getColor(current_color, self, "选择颜色")
        
        if color.isValid():
            self.config[config_key] = color.name()
            
            # 更新对应的标签
            if config_key == 'header_bg_color':
                self._update_color_label(self.header_bg_label, color.name())
            elif config_key == 'header_text_color':
                self._update_color_label(self.header_text_label, color.name())
            elif config_key == 'own_brand_bg_color':
                self._update_color_label(self.own_brand_label, color.name())
    
    def _on_preset_changed(self, index):
        """预设风格改变"""
        presets = {
            0: {  # 商务蓝
                'preset': 'business_blue',
                'header_bg_color': '#4472C4',
                'header_text_color': '#FFFFFF',
                'own_brand_bg_color': '#FFF2CC'
            },
            1: {  # 清新绿
                'preset': 'fresh_green',
                'header_bg_color': '#70AD47',
                'header_text_color': '#FFFFFF',
                'own_brand_bg_color': '#E2EFDA'
            },
            2: {  # 强对比黄
                'preset': 'high_contrast',
                'header_bg_color': '#FFC000',
                'header_text_color': '#000000',
                'own_brand_bg_color': '#FFFF00'
            }
        }
        
        if index in presets:
            preset_config = presets[index]
            self.config.update(preset_config)
            
            # 更新颜色标签
            self._update_color_label(self.header_bg_label, self.config['header_bg_color'])
            self._update_color_label(self.header_text_label, self.config['header_text_color'])
            self._update_color_label(self.own_brand_label, self.config['own_brand_bg_color'])
    
    def _save_config(self):
        """保存配置"""
        # 收集所有配置
        self.config['border_width'] = float(self.border_width_spin.value())
        self.config['image_width'] = self.image_width_spin.value()
        self.config['dpi'] = int(self.dpi_combo.currentText())
        self.config['font_name'] = self.font_combo.currentText()
        self.config['font_size'] = self.font_size_spin.value()
        
        # 保存到数据库
        if self.db_manager.save_config('table_style', self.config):
            logger.info("表格样式配置保存成功")
            self.accept()
        else:
            logger.error("表格样式配置保存失败")

