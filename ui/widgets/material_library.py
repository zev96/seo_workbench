"""
素材库面板
采用 Fluent Design 侧边导航栏风格
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidgetItem, 
    QInputDialog, QDialog, QTextEdit, QDialogButtonBox, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QSize
from PyQt6.QtGui import QIcon, QDrag
from qfluentwidgets import (
    TreeWidget, SearchLineEdit, PushButton, ToolButton, TransparentToolButton,
    FluentIcon as FIF, RoundMenu, Action, MessageBox, InfoBar, InfoBarPosition
)
from loguru import logger

from ...database.db_manager import DatabaseManager


class MaterialTreeWidget(TreeWidget):
    """自定义树形控件，支持拖拽素材内容"""
    
    def startDrag(self, supportedActions):
        """重写拖拽开始方法"""
        item = self.currentItem()
        if not item:
            return
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("type") != "material":
            return
        
        # 创建 MIME 数据，包含素材内容
        mime_data = QMimeData()
        mime_data.setText(data.get("content", ""))
        
        # 创建拖拽对象
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        
        # 执行拖拽
        drag.exec(Qt.DropAction.CopyAction)


class MultiLineInputDialog(QDialog):
    """多行文本输入对话框"""
    
    def __init__(self, title: str, label: str, text: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(500, 300)
        
        layout = QVBoxLayout(self)
        
        # 标签
        layout.addWidget(QLabel(label))
        
        # 文本编辑器
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(text)
        layout.addWidget(self.text_edit)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_text(self) -> str:
        return self.text_edit.toPlainText()


class MaterialLibrary(QWidget):
    """素材库组件 (Fluent 风格)"""
    
    # 信号定义
    material_selected = pyqtSignal(int)  # 素材被选中
    import_excel_clicked = pyqtSignal()  # 导入 Excel
    clear_grid_clicked = pyqtSignal()    # 清空工作区
    bold_tool_clicked = pyqtSignal()     # 批量加粗设置
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.current_category = None
        self._init_ui()
        self._load_categories()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # 搜索框
        self.search_input = SearchLineEdit()
        self.search_input.setPlaceholderText("搜索素材...")
        self.search_input.textChanged.connect(self._on_search)
        layout.addWidget(self.search_input)
        
        # 树形列表 (整合分类和素材) - 使用自定义 TreeWidget
        self.tree = MaterialTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        
        # 启用拖拽
        self.tree.setDragEnabled(True)
        self.tree.setDragDropMode(MaterialTreeWidget.DragDropMode.DragOnly)
        
        layout.addWidget(self.tree)
        
        # 底部按钮组
        btn_layout = QHBoxLayout()
        
        self.add_category_btn = PushButton(FIF.ADD, "新增分类")
        self.add_category_btn.clicked.connect(self._on_add_category)
        btn_layout.addWidget(self.add_category_btn)
        
        self.add_btn = PushButton(FIF.ADD, "新增素材")
        self.add_btn.clicked.connect(self._on_add_material)
        btn_layout.addWidget(self.add_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_categories(self):
        """加载分类和素材"""
        self.tree.clear()
        categories = self.db_manager.get_all_categories()
        
        # 分组处理
        groups = {}
        for cat in categories:
            prefix = cat.split('-')[0] if '-' in cat else '其他'
            if prefix not in groups:
                groups[prefix] = []
            groups[prefix].append(cat)
        
        for group_name, cats in sorted(groups.items()):
            # 创建一级分类（组）
            group_item = QTreeWidgetItem([f"📁 {group_name}"])
            group_item.setExpanded(True)
            group_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "group", "name": group_name})
            self.tree.addTopLevelItem(group_item)
            
            for cat in sorted(cats):
                # 创建二级分类
                cat_item = QTreeWidgetItem([f"  📂 {cat}"])
                cat_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "category", "name": cat})
                group_item.addChild(cat_item)
                
                # 加载该分类下的素材
                self._load_materials_for_item(cat_item, cat)
    
    def _load_materials_for_item(self, parent_item: QTreeWidgetItem, category: str):
        """加载指定分类的素材到树节点"""
        materials = self.db_manager.get_materials_by_category(category)
        for mat in materials:
            # 显示前 30 个字符
            preview = mat.content[:30].replace('\n', ' ') + "..."
            item = QTreeWidgetItem([f"    📄 {preview}"])
            item.setData(0, Qt.ItemDataRole.UserRole, {
                "type": "material",
                "id": mat.id,
                "content": mat.content,
                "category": category
            })
            item.setToolTip(0, mat.content)
            parent_item.addChild(item)
    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """项被点击"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
            
        if data["type"] == "category":
            self.current_category = data["name"]
        elif data["type"] == "material":
            self.current_category = data["category"]
            self.material_selected.emit(data["id"])
    
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """双击事件 - 编辑"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data["type"] == "material":
            self._on_edit_material()
    
    def _on_search(self, text: str):
        """搜索过滤"""
        if not text:
            self._load_categories()
            return
        
        # 搜索素材
        self.tree.clear()
        materials = self.db_manager.search_materials(text)
        
        if materials:
            search_item = QTreeWidgetItem([f"🔍 搜索结果 ({len(materials)} 条)"])
            search_item.setExpanded(True)
            self.tree.addTopLevelItem(search_item)
            
            for mat in materials:
                preview = mat.content[:40].replace('\n', ' ') + "..."
                item = QTreeWidgetItem([f"  [{mat.category}] {preview}"])
                item.setData(0, Qt.ItemDataRole.UserRole, {
                    "type": "material",
                    "id": mat.id,
                    "content": mat.content,
                    "category": mat.category
                })
                item.setToolTip(0, mat.content)
                search_item.addChild(item)
    
    def _show_context_menu(self, pos):
        """右键菜单"""
        item = self.tree.itemAt(pos)
        if not item:
            # 空白处点击：新增分类
            menu = RoundMenu(parent=self)
            menu.addAction(Action(FIF.ADD, "新增分类", triggered=self._on_add_category))
            menu.exec(self.tree.mapToGlobal(pos))
            return
            
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
            
        menu = RoundMenu(parent=self)
        
        if data["type"] == "group":
            menu.addAction(Action(FIF.ADD, "新增子分类", triggered=lambda: self._on_add_subcategory(data["name"])))
        elif data["type"] == "category":
            menu.addAction(Action(FIF.ADD, "新增素材", triggered=self._on_add_material))
            menu.addAction(Action(FIF.DELETE, "删除分类", triggered=self._on_delete_category))
        elif data["type"] == "material":
            menu.addAction(Action(FIF.EDIT, "编辑", triggered=self._on_edit_material))
            menu.addAction(Action(FIF.DELETE, "删除", triggered=self._on_delete_material))
            
        menu.exec(self.tree.mapToGlobal(pos))
    
    def _on_add_category(self):
        """新增大类"""
        text, ok = QInputDialog.getText(self, "新增大类", "请输入大类名称（如：通用、洗地机）:")
        if ok and text:
            # 创建一个示例分类
            category_name = f"{text}-示例"
            self.db_manager.add_material(category_name, "示例素材", "")
            self._load_categories()
            
            InfoBar.success(
                title='创建成功',
                content=f'已创建大类 "{text}"',
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self.window()
            )
    
    def _on_add_subcategory(self, group_name: str):
        """新增子分类"""
        text, ok = QInputDialog.getText(
            self, 
            "新增子分类", 
            f"请输入 {group_name} 下的子分类名称（如：开头、结尾）:"
        )
        if ok and text:
            category_name = f"{group_name}-{text}"
            self.db_manager.add_material(category_name, "示例素材", "")
            self._load_categories()
            
            InfoBar.success(
                title='创建成功',
                content=f'已创建分类 "{category_name}"',
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self.window()
            )
    
    def _on_add_material(self):
        """新增素材"""
        if not self.current_category:
            InfoBar.warning(
                title='提示',
                content='请先选择一个分类',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self.window()
            )
            return
        
        dialog = MultiLineInputDialog("新增素材", "请输入素材内容:", "", self)
        if dialog.exec():
            text = dialog.get_text()
            if text:
                self.db_manager.add_material(self.current_category, text, "")
                self._load_categories()
                
                InfoBar.success(
                    title='添加成功',
                    content='素材已添加',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=False,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=2000,
                    parent=self.window()
                )
    
    def _on_edit_material(self):
        """编辑素材"""
        item = self.tree.currentItem()
        if not item: 
            return
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data["type"] != "material": 
            return
        
        dialog = MultiLineInputDialog("编辑素材", "内容:", data["content"], self)
        if dialog.exec():
            text = dialog.get_text()
            if text:
                self.db_manager.update_material(data["id"], content=text)
                self._load_categories()
                
                InfoBar.success(
                    title='保存成功',
                    content='素材已更新',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=False,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=2000,
                    parent=self.window()
                )
    
    def _on_delete_category(self):
        """删除分类"""
        item = self.tree.currentItem()
        if not item:
            return
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data["type"] != "category":
            return
        
        # 确认对话框
        w = MessageBox("确认删除", f"确定要删除分类 '{data['name']}' 及其所有素材吗？", self.window())
        if w.exec():
            try:
                # 删除该分类下的所有素材
                materials = self.db_manager.get_materials_by_category(data['name'])
                for mat in materials:
                    self.db_manager.delete_material(mat.id)
                
                self._load_categories()
                
                InfoBar.success(
                    title='删除成功',
                    content=f'已删除分类 "{data["name"]}"',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=False,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=2000,
                    parent=self.window()
                )
            except Exception as e:
                logger.error(f"删除分类失败: {e}")
                InfoBar.error(
                    title='删除失败',
                    content=str(e),
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=3000,
                    parent=self.window()
                )

    def _on_delete_material(self):
        """删除素材"""
        item = self.tree.currentItem()
        if not item:
            return
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data["type"] != "material":
            return
        
        # 确认对话框
        w = MessageBox("确认删除", "确定要删除这条素材吗？", self.window())
        if w.exec():
            try:
                self.db_manager.delete_material(data["id"])
                self._load_categories()
                
                InfoBar.success(
                    title='删除成功',
                    content='素材已删除',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=False,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=2000,
                    parent=self.window()
                )
            except Exception as e:
                logger.error(f"删除素材失败: {e}")
                InfoBar.error(
                    title='删除失败',
                    content=str(e),
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=3000,
                    parent=self.window()
                )
