"""
混排策略配置对话框
"""
from typing import Callable, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QSplitter
)
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    CardWidget, StrongBodyLabel, BodyLabel, LineEdit, SpinBox,
    SwitchButton, PrimaryPushButton, PushButton, ListWidget,
    FluentIcon as FIF, InfoBar, InfoBarPosition, MessageBox
)
from loguru import logger

from ...config.settings import ProfileConfig, ShufflingStrategy


class StrategyConfigDialog(QDialog):
    """混排策略配置对话框"""
    
    def __init__(self, config: ProfileConfig, validator: Optional[Callable] = None, parent=None):
        super().__init__(parent)
        self.config = config
        self.validator = validator
        self._current_mode = 'add'
        self._init_ui()
        self._load_strategies()
        
    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle("随机组设置")
        self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 使用 Splitter 实现左右布局（无标题，直接内容区）
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)  # 分割线宽度
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #E5E5E5;
            }
        """)
        
        # === 左侧：策略列表（浅灰背景） ===
        left_widget = QWidget()
        left_widget.setStyleSheet("""
            QWidget {
                background-color: #F7F9FB;
            }
        """)
        left_widget.setFixedWidth(220)  # 固定宽度
        
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(15, 20, 15, 15)
        left_layout.setSpacing(12)
        
        # 标题标签
        list_label = BodyLabel("已保存的组合")
        list_label.setStyleSheet("font-weight: 500; color: #666666; font-size: 12px;")
        left_layout.addWidget(list_label)
        
        # 策略列表
        self.strategy_list = ListWidget()
        self.strategy_list.itemClicked.connect(self._on_strategy_selected)
        self.strategy_list.setStyleSheet("""
            ListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            ListWidget::item {
                background-color: transparent;
                border-radius: 8px;
                padding: 10px 12px;
                margin: 2px 0px;
                color: #666666;
                border: none;
            }
            ListWidget::item:hover {
                background-color: rgba(71, 132, 209, 0.1);
                color: #4784d1;
            }
            ListWidget::item:selected {
                background-color: #FFFFFF;
                color: #1F1F1F;
                font-weight: 500;
                border-left: 3px solid #4784d1;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            }
        """)
        left_layout.addWidget(self.strategy_list)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        self.add_btn = PushButton("添加")
        self.add_btn.clicked.connect(self._on_add_strategy)
        self.add_btn.setStyleSheet("""
            PushButton {
                background-color: #FFFFFF;
                border: 1px solid #E5E5E5;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            PushButton:hover {
                background-color: #F0F0F0;
                border-color: #4784d1;
            }
        """)
        btn_layout.addWidget(self.add_btn)
        
        self.remove_btn = PushButton("删除")
        self.remove_btn.clicked.connect(self._on_remove_strategy)
        self.remove_btn.setStyleSheet("""
            PushButton {
                background-color: #FFFFFF;
                border: 1px solid #E5E5E5;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            PushButton:hover {
                background-color: #FFF0F0;
                border-color: #FF4444;
                color: #FF4444;
            }
        """)
        btn_layout.addWidget(self.remove_btn)
        
        left_layout.addLayout(btn_layout)
        
        splitter.addWidget(left_widget)
        
        # === 右侧：策略详情（白色背景） ===
        right_widget = QWidget()
        right_widget.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
            }
        """)
        
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(25, 20, 25, 20)
        right_layout.setSpacing(15)
        
        # 详情标题
        detail_title = StrongBodyLabel("组合配置")
        detail_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #1F1F1F;")
        right_layout.addWidget(detail_title)
        
        # 表单区域卡片
        form_card = CardWidget()
        form_card.setStyleSheet("""
            CardWidget {
                background-color: #FAFBFC;
                border-radius: 12px;
                border: 1px solid #E8EAED;
            }
        """)
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(18)
        
        # 1. 名称
        name_layout = QVBoxLayout()
        name_layout.setSpacing(6)
        name_label = BodyLabel("组合名称")
        name_label.setStyleSheet("font-weight: 500; color: #666666; font-size: 13px;")
        name_layout.addWidget(name_label)
        
        self.name_input = LineEdit()
        self.name_input.setPlaceholderText("例如：品牌组")
        self.name_input.setMinimumWidth(400)
        self.name_input.setMinimumHeight(40)
        self.name_input.setStyleSheet("""
            LineEdit {
                background-color: #FFFFFF;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
            }
            LineEdit:focus {
                border-color: #4784d1;
            }
        """)
        name_layout.addWidget(self.name_input)
        form_layout.addLayout(name_layout)
        
        # 2. 列
        columns_layout = QVBoxLayout()
        columns_layout.setSpacing(6)
        columns_label = BodyLabel("列范围")
        columns_label.setStyleSheet("font-weight: 500; color: #666666; font-size: 13px;")
        columns_layout.addWidget(columns_label)
        
        self.columns_input = LineEdit()
        self.columns_input.setPlaceholderText("例如：2,3,5-8")
        self.columns_input.setMinimumWidth(400)
        self.columns_input.setMinimumHeight(30)
        self.columns_input.setStyleSheet("""
            LineEdit {
                background-color: #FFFFFF;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
            }
            LineEdit:focus {
                border-color: #4784d1;
            }
        """)
        columns_layout.addWidget(self.columns_input)
        form_layout.addLayout(columns_layout)
        
        # 3. 组大小和保留数（横向排列）
        params_layout = QHBoxLayout()
        params_layout.setSpacing(15)
        
        # 组大小
        size_layout = QVBoxLayout()
        size_layout.setSpacing(6)
        size_label = BodyLabel("每组列数")
        size_label.setStyleSheet("font-weight: 500; color: #666666; font-size: 13px;")
        size_layout.addWidget(size_label)
        
        self.group_size_spin = SpinBox()
        self.group_size_spin.setRange(1, 20)
        self.group_size_spin.setValue(2)
        self.group_size_spin.setStyleSheet("""
            SpinBox {
                background-color: #FFFFFF;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px 10px;
            }
        """)
        size_layout.addWidget(self.group_size_spin)
        params_layout.addLayout(size_layout)
        
        # 保留数
        keep_layout = QVBoxLayout()
        keep_layout.setSpacing(6)
        keep_label = BodyLabel("保留组数")
        keep_label.setStyleSheet("font-weight: 500; color: #666666; font-size: 13px;")
        keep_layout.addWidget(keep_label)
        
        self.keep_count_spin = SpinBox()
        self.keep_count_spin.setRange(1, 50)
        self.keep_count_spin.setValue(1)
        self.keep_count_spin.setStyleSheet("""
            SpinBox {
                background-color: #FFFFFF;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px 10px;
            }
        """)
        keep_layout.addWidget(self.keep_count_spin)
        params_layout.addLayout(keep_layout)
        
        form_layout.addLayout(params_layout)
        
        # 4. 打乱顺序
        shuffle_layout = QHBoxLayout()
        shuffle_layout.setSpacing(12)
        shuffle_label = BodyLabel("打乱顺序")
        shuffle_label.setStyleSheet("font-weight: 500; color: #666666; font-size: 13px;")
        shuffle_layout.addWidget(shuffle_label)
        
        self.shuffle_switch = SwitchButton()
        self.shuffle_switch.setChecked(False)
        shuffle_layout.addWidget(self.shuffle_switch)
        shuffle_layout.addStretch()
        form_layout.addLayout(shuffle_layout)
        
        right_layout.addWidget(form_card)
        
        # 保存策略按钮
        save_strategy_layout = QHBoxLayout()
        save_strategy_layout.addStretch()
        self.save_strategy_btn = PrimaryPushButton("保存组合")
        self.save_strategy_btn.clicked.connect(self._on_save_strategy)
        self.save_strategy_btn.setFixedHeight(38)
        self.save_strategy_btn.setStyleSheet("""
            PrimaryPushButton {
                background-color: #4784d1;
                border: none;
                border-radius: 8px;
                padding: 0px 24px;
                font-size: 13px;
                font-color: #FFFFFF;
                font-weight: 500;
            }
            PrimaryPushButton:hover {
                background-color: #3a6fb8;
            }
            PrimaryPushButton:pressed {
                background-color: #2d5a99;
            }
        """)
        save_strategy_layout.addWidget(self.save_strategy_btn)
        right_layout.addLayout(save_strategy_layout)
        
        right_layout.addStretch()
        
        splitter.addWidget(right_widget)
        
        layout.addWidget(splitter)
        
        # === 底部：确认区（白色背景） ===
        bottom_widget = QWidget()
        bottom_widget.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-top: 1px solid #E5E5E5;
            }
        """)
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(20, 15, 20, 15)
        bottom_layout.setSpacing(12)
        bottom_layout.addStretch()
        
        self.cancel_btn = PushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setFixedSize(100, 36)
        self.cancel_btn.setStyleSheet("""
            PushButton {
                background-color: #F5F5F5;
                border: none;
                border-radius: 8px;
                color: #666666;
                font-size: 13px;
            }
            PushButton:hover {
                background-color: #E8E8E8;
            }
        """)
        bottom_layout.addWidget(self.cancel_btn)
        
        self.confirm_btn = PrimaryPushButton("保存生效")
        self.confirm_btn.clicked.connect(self.accept)
        self.confirm_btn.setFixedSize(120, 36)
        self.confirm_btn.setStyleSheet("""
            PrimaryPushButton {
                background-color: #4784d1;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 13px;
                font-weight: 500;
            }
            PrimaryPushButton:hover {
                background-color: #3a6fb8;
            }
            PrimaryPushButton:pressed {
                background-color: #2d5a99;
            }
        """)
        bottom_layout.addWidget(self.confirm_btn)
        
        layout.addWidget(bottom_widget)
    
    def _load_strategies(self):
        """加载策略列表"""
        self.strategy_list.clear()
        for strategy in self.config.shuffling_strategies:
            self.strategy_list.addItem(strategy.name)
    
    def _on_add_strategy(self):
        """添加新策略"""
        self._current_mode = 'add'
        self.strategy_list.setCurrentItem(None)
        self.name_input.clear()
        self.columns_input.clear()
        self.group_size_spin.setValue(2)
        self.keep_count_spin.setValue(1)
        self.shuffle_switch.setChecked(False)
        
        InfoBar.info(
            title='提示',
            content='请填写新策略的参数',
            orient=Qt.Orientation.Horizontal,
            isClosable=False,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=2000,
            parent=self
        )
    
    def _on_strategy_selected(self, item):
        """策略被选中"""
        self._current_mode = 'edit'
        strategy_name = item.text()
        
        # 查找策略
        strategy = None
        for s in self.config.shuffling_strategies:
            if s.name == strategy_name:
                strategy = s
                break
        
        if not strategy:
            return
        
        # 填充表单
        self.name_input.setText(strategy.name)
        self.columns_input.setText(",".join(map(str, strategy.columns)))
        self.group_size_spin.setValue(strategy.group_size)
        self.keep_count_spin.setValue(strategy.keep_count)
        self.shuffle_switch.setChecked(strategy.shuffle_order)
    
    def _on_save_strategy(self):
        """保存策略"""
        name = self.name_input.text().strip()
        if not name:
            MessageBox("提示", "请输入策略名称", self).exec()
            return
        
        columns_text = self.columns_input.text().strip()
        if not columns_text:
            MessageBox("提示", "请输入涉及的列", self).exec()
            return
        
        # 解析列号
        try:
            columns = self._parse_columns(columns_text)
            if not columns:
                MessageBox("提示", "列号格式不正确", self).exec()
                return
        except Exception as e:
            MessageBox("提示", f"列号解析失败: {e}", self).exec()
            return
        
        # 外部验证（检查列号是否合法）
        if self.validator:
            is_valid, error_msg = self.validator(columns)
            if not is_valid:
                MessageBox("验证失败", error_msg, self).exec()
                return
        
        # 创建策略对象
        try:
            strategy = ShufflingStrategy(
                name=name,
                columns=columns,
                group_size=self.group_size_spin.value(),
                keep_count=self.keep_count_spin.value(),
                shuffle_order=self.shuffle_switch.isChecked()
            )
        except Exception as e:
            MessageBox("提示", f"策略参数不合法: {e}", self).exec()
            return
        
        # 根据模式添加或更新
        if self._current_mode == 'add':
            # 检查是否重名
            if any(s.name == name for s in self.config.shuffling_strategies):
                MessageBox("提示", f"策略名称 '{name}' 已存在", self).exec()
                return
            
            self.config.shuffling_strategies.append(strategy)
            logger.info(f"新增策略: {name}")
        else:
            # 编辑模式：找到并替换
            for i, s in enumerate(self.config.shuffling_strategies):
                if s.name == name:
                    self.config.shuffling_strategies[i] = strategy
                    logger.info(f"更新策略: {name}")
                    break
        
        # 保存配置
        self.config.save_config()
        
        # 刷新列表
        self._load_strategies()
        
        InfoBar.success(
            title='保存成功',
            content=f'策略 "{name}" 已保存',
            orient=Qt.Orientation.Horizontal,
            isClosable=False,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=2000,
            parent=self
        )
    
    def _on_remove_strategy(self):
        """删除选中的策略"""
        current_item = self.strategy_list.currentItem()
        if not current_item:
            InfoBar.warning(
                title='提示',
                content='请先选择要删除的策略',
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self
            )
            return
        
        # 确认删除
        w = MessageBox("确认删除", f"确定要删除策略 '{current_item.text()}' 吗？", self)
        if w.exec():
            # 找到并删除策略
            strategy_name = current_item.text()
            self.config.shuffling_strategies = [
                s for s in self.config.shuffling_strategies 
                if s.name != strategy_name
            ]
            self.config.save_config()
            
            # 刷新列表
            self._load_strategies()
            
            # 清空表单
            self.name_input.clear()
            self.columns_input.clear()
            
            InfoBar.success(
                title='删除成功',
                content=f'策略 "{strategy_name}" 已删除',
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self
            )
            
            logger.info(f"删除策略: {strategy_name}")
    
    def _parse_columns(self, text: str) -> list[int]:
        """
        解析列号字符串，支持范围
        例如: "2,3,5-8" -> [2, 3, 5, 6, 7, 8]
        """
        columns = []
        parts = text.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                # 范围
                start, end = part.split('-')
                start, end = int(start.strip()), int(end.strip())
                columns.extend(range(start, end + 1))
            else:
                # 单个数字
                columns.append(int(part))
        
        return sorted(list(set(columns)))  # 去重并排序
