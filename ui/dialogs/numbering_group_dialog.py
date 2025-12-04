"""
序号分组设置对话框
"""
from typing import List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget
)
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    CardWidget, StrongBodyLabel, BodyLabel, LineEdit,
    PrimaryPushButton, PushButton, ListWidget,
    FluentIcon as FIF, InfoBar, InfoBarPosition, MessageBox
)
from loguru import logger

from ...config.settings import ProfileConfig


class NumberingGroupDialog(QDialog):
    """序号分组设置对话框"""
    
    def __init__(self, config: ProfileConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self._init_ui()
        self._load_groups()
        
    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle("序号分组设置")
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题和说明
        title = StrongBodyLabel("序号独立计数区间")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1F1F1F;")
        layout.addWidget(title)
        
        desc = BodyLabel("为不同的列区域设置独立的序号计数器，每个区间的序号从1开始，互不干扰。")
        desc.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(desc)
        
        # 示例说明
        example_card = CardWidget()
        example_card.setStyleSheet("""
            CardWidget {
                background-color: #F0F8FF;
                border-radius: 8px;
                border: 1px solid #B0D4F1;
            }
        """)
        example_layout = QVBoxLayout(example_card)
        example_layout.setContentsMargins(12, 12, 12, 12)
        
        example_label = BodyLabel("💡 示例：输入 8-21 表示Excel第8列到第21列独立计数（列号从1开始）")
        example_label.setStyleSheet("color: #0066CC; font-size: 11px;")
        example_layout.addWidget(example_label)
        layout.addWidget(example_card)
        
        # 分组列表
        list_label = BodyLabel("已配置的分组")
        list_label.setStyleSheet("font-weight: 500; color: #666666; font-size: 13px; margin-top: 10px;")
        layout.addWidget(list_label)
        
        self.group_list = ListWidget()
        self.group_list.setStyleSheet("""
            ListWidget {
                background-color: #FAFBFC;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 5px;
            }
            ListWidget::item {
                background-color: #FFFFFF;
                border-radius: 6px;
                padding: 10px;
                margin: 3px;
                color: #333333;
            }
            ListWidget::item:hover {
                background-color: #F0F0F0;
            }
            ListWidget::item:selected {
                background-color: #E3F2FD;
                color: #1976D2;
            }
        """)
        layout.addWidget(self.group_list)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.add_btn = PushButton("添加分组", self, FIF.ADD)
        self.add_btn.clicked.connect(self._on_add_group)
        btn_layout.addWidget(self.add_btn)
        
        self.remove_btn = PushButton("删除分组", self, FIF.DELETE)
        self.remove_btn.clicked.connect(self._on_remove_group)
        btn_layout.addWidget(self.remove_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 添加分组表单
        form_card = CardWidget()
        form_card.setStyleSheet("""
            CardWidget {
                background-color: #FAFBFC;
                border-radius: 8px;
                border: 1px solid #E0E0E0;
            }
        """)
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)
        
        input_label = BodyLabel("列范围（Excel列号，从1开始，逗号或短横线分隔）")
        input_label.setStyleSheet("font-weight: 500; color: #666666; font-size: 12px;")
        form_layout.addWidget(input_label)
        
        self.columns_input = LineEdit()
        self.columns_input.setPlaceholderText("例如：8-21 或 8,9,10,11")
        self.columns_input.setStyleSheet("""
            LineEdit {
                background-color: #FFFFFF;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 12px;
            }
            LineEdit:focus {
                border-color: #4784d1;
            }
        """)
        form_layout.addWidget(self.columns_input)
        
        layout.addWidget(form_card)
        
        # 底部按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        
        self.cancel_btn = PushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(self.cancel_btn)
        
        self.save_btn = PrimaryPushButton("保存配置")
        self.save_btn.clicked.connect(self._on_save)
        bottom_layout.addWidget(self.save_btn)
        
        layout.addLayout(bottom_layout)
        
    def _load_groups(self):
        """加载已有的分组"""
        self.group_list.clear()
        for group in self.config.numbering_groups:
            display_text = f"分组: {self._format_group(group)}"
            self.group_list.addItem(display_text)
    
    def _format_group(self, group: List[int]) -> str:
        """格式化分组显示（内部存储的是代码索引，显示时转换为Excel列号）"""
        if not group:
            return "空"
        
        # 尝试识别连续区间（显示时+1转换为Excel列号）
        group_sorted = sorted(group)
        ranges = []
        start = group_sorted[0] + 1  # 转换为Excel列号
        end = group_sorted[0] + 1
        
        for i in range(1, len(group_sorted)):
            current = group_sorted[i] + 1  # 转换为Excel列号
            if current == end + 1:
                end = current
            else:
                if start == end:
                    ranges.append(f"{start}")
                else:
                    ranges.append(f"{start}-{end}")
                start = current
                end = current
        
        # 添加最后一个范围
        if start == end:
            ranges.append(f"{start}")
        else:
            ranges.append(f"{start}-{end}")
        
        return ", ".join(ranges)
    
    def _parse_columns(self, text: str) -> List[int]:
        """解析列范围输入（用户输入Excel列号，从1开始；内部存储代码索引，从0开始）"""
        columns = []
        parts = text.replace('，', ',').split(',')
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            if '-' in part:
                # 范围格式：8-21（Excel列号）
                try:
                    start, end = part.split('-')
                    start = int(start.strip())
                    end = int(end.strip())
                    if start < 1 or end < 1:
                        raise ValueError(f"列号必须大于0: {part}")
                    # 转换为代码索引（减1）
                    columns.extend(range(start - 1, end))
                except ValueError as e:
                    raise e
                except:
                    raise ValueError(f"无效的范围格式: {part}")
            else:
                # 单个列（Excel列号）
                try:
                    col = int(part)
                    if col < 1:
                        raise ValueError(f"列号必须大于0: {part}")
                    # 转换为代码索引（减1）
                    columns.append(col - 1)
                except ValueError as e:
                    raise e
                except:
                    raise ValueError(f"无效的列号: {part}")
        
        return sorted(list(set(columns)))
    
    def _on_add_group(self):
        """添加分组"""
        text = self.columns_input.text().strip()
        if not text:
            InfoBar.warning(
                title="输入为空",
                content="请输入列范围",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
        
        try:
            columns = self._parse_columns(text)
            if not columns:
                raise ValueError("未解析到有效的列")
            
            # 检查是否与现有分组冲突
            for existing_group in self.config.numbering_groups:
                overlap = set(columns) & set(existing_group)
                if overlap:
                    # 显示时转换为Excel列号
                    overlap_excel = sorted([col + 1 for col in overlap])
                    InfoBar.warning(
                        title="列冲突",
                        content=f"列 {overlap_excel} 已在其他分组中",
                        parent=self,
                        position=InfoBarPosition.TOP
                    )
                    return
            
            # 添加到配置
            self.config.numbering_groups.append(columns)
            self._load_groups()
            self.columns_input.clear()
            
            InfoBar.success(
                title="添加成功",
                content=f"已添加分组: {self._format_group(columns)}",
                parent=self,
                position=InfoBarPosition.TOP
            )
            
        except Exception as e:
            InfoBar.error(
                title="解析错误",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP
            )
    
    def _on_remove_group(self):
        """删除选中的分组"""
        current_row = self.group_list.currentRow()
        if current_row < 0:
            InfoBar.warning(
                title="未选择分组",
                content="请先选择要删除的分组",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
        
        # 确认删除
        msg_box = MessageBox(
            "确认删除",
            f"确定要删除分组 {current_row + 1} 吗？",
            self
        )
        if msg_box.exec():
            del self.config.numbering_groups[current_row]
            self._load_groups()
            
            InfoBar.success(
                title="删除成功",
                content="已删除分组",
                parent=self,
                position=InfoBarPosition.TOP
            )
    
    def _on_save(self):
        """保存配置"""
        try:
            self.config.save_config()
            InfoBar.success(
                title="保存成功",
                content=f"已保存 {len(self.config.numbering_groups)} 个序号分组",
                parent=self,
                position=InfoBarPosition.TOP
            )
            self.accept()
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            InfoBar.error(
                title="保存失败",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP
            )

