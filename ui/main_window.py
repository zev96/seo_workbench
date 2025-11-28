"""
主窗口
SEO 工作台的主界面，采用 Fluent Design 风格
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from qfluentwidgets import (
    MSFluentWindow, SplitFluentWindow, NavigationItemPosition,
    FluentIcon as FIF, SplashScreen
)
from loguru import logger

from .widgets.material_library import MaterialLibrary
from .widgets.smart_grid import SmartGrid
from .widgets.strategy_panel import StrategyPanel
from .widgets.toolbar import Toolbar
from .widgets.log_panel import LogPanel
from .dialogs.api_settings import APISettingsDialog
from .dialogs.ai_title_dialog import AITitleDialog
from .dialogs.strategy_config_dialog import StrategyConfigDialog
from .dialogs.seo_setting_dialog import SEOSettingDialog
from ..config.settings import ProfileConfig
from ..database.db_manager import DatabaseManager


class MainWindow(MSFluentWindow):
    """主窗口类 (Fluent 风格)"""
    
    def __init__(self, config: ProfileConfig, db_manager: DatabaseManager):
        super().__init__()
        
        self.config = config
        self.db_manager = db_manager
        
        # AI 标题队列（用于标题驱动混排）
        self.ai_title_queue = []
        self.ai_title_format = "H1"
        
        self._init_window()
        self._init_ui()
        self._connect_signals()
        
        logger.info("Fluent 主窗口初始化完成")
    
    def _init_window(self):
        """初始化窗口属性"""
        self.setWindowTitle("SEO 智能内容工作台")
        self.resize(1400, 900)
        
        # 设置窗口图标（这里暂时使用默认）
        # self.setWindowIcon(QIcon('resources/icons/app.ico'))
        
        # 开启 Mica 效果（Windows 11 毛玻璃背景）
        try:
            from qfluentwidgets import setTheme, Theme, setThemeColor
            from PyQt6.QtGui import QColor
            
            # 设置主题颜色为深天蓝
            setThemeColor(QColor("#4784d1"))
            
            # 开启 Mica 效果
            self.setMicaEffectEnabled(True)
            
            logger.info("Mica 毛玻璃效果已启用")
        except Exception as e:
            logger.warning(f"无法启用 Mica 效果: {e}")
        
        # 居中显示
        desktop = self.screen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
    
    def _init_ui(self):
        """初始化 UI"""
        # 创建中心部件容器
        self.central_widget = QWidget()
        self.central_widget.setObjectName("central_widget")
        self.addSubInterface(self.central_widget, FIF.HOME, "工作台")
        
        # 主布局 (垂直：工具栏 + 内容 + 日志)
        # 增加 margins 营造呼吸感
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 1. 顶部工具栏
        self.toolbar = Toolbar(self.config)
        main_layout.addWidget(self.toolbar)
        
        # 2. 中间内容区（三栏布局）
        # 使用 QSplitter 实现可调节的三栏
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setHandleWidth(5)
        content_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background-color: #009faa;
            }
        """)
        
        # 左侧：素材库
        self.material_library = MaterialLibrary(self.db_manager)
        content_splitter.addWidget(self.material_library)
        
        # 中间：网格编辑器
        self.smart_grid = SmartGrid(self.config)
        content_splitter.addWidget(self.smart_grid)
        
        # 右侧：策略面板
        self.strategy_panel = StrategyPanel(self.config)
        self.strategy_panel.set_validator(self._validate_strategy_columns)
        content_splitter.addWidget(self.strategy_panel)
        
        # 设置分割器比例（左:中:右 = 2:5:2）
        content_splitter.setStretchFactor(0, 20)
        content_splitter.setStretchFactor(1, 60)
        content_splitter.setStretchFactor(2, 20)
        
        main_layout.addWidget(content_splitter)
        
        # 3. 底部：日志面板（隐藏，用户不需要）
        # self.log_panel = LogPanel()
        # main_layout.addWidget(self.log_panel)
        
        # 添加其他导航项（设置页）
        # self.navigationInterface.addSeparator()
        
        self.navigationInterface.addItem(
            routeKey='settings',
            icon=FIF.SETTING,
            text='设置',
            onClick=self._on_api_settings,
            position=NavigationItemPosition.BOTTOM
        )
        
        self.navigationInterface.addItem(
            routeKey='about',
            icon=FIF.INFO,
            text='关于',
            onClick=self._on_about,
            position=NavigationItemPosition.BOTTOM
        )
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 工具栏信号
        self.toolbar.generate_clicked.connect(self._on_generate)
        
        # 策略面板信号（右下角按钮）
        self.strategy_panel.import_excel_clicked.connect(self._on_import_excel)
        self.strategy_panel.clear_grid_clicked.connect(self.smart_grid.clear_all)
        self.strategy_panel.bold_tool_clicked.connect(self._on_bold_tool)
        self.strategy_panel.ai_title_clicked.connect(self._on_ai_title_dialog)
        self.strategy_panel.strategy_config_clicked.connect(self._on_strategy_config)
        self.strategy_panel.seo_config_clicked.connect(self._on_seo_config)
        
        # 素材库信号
        self.material_library.material_selected.connect(self._on_material_selected)
        
        # 网格信号
        self.smart_grid.data_changed.connect(self._on_grid_data_changed)
    
    def _validate_strategy_columns(self, columns: list[int]) -> tuple[bool, str]:
        """验证策略列号是否合法"""
        # 检查是否有数据
        active_rows = self.smart_grid.get_active_row_count()
        if active_rows == 0 and self.smart_grid.table.rowCount() == 0:
             # 如果连空表格都没有，或者没有任何内容
             # 实际上 SmartGrid 初始化时会创建表格，但可能是隐藏的
             # 我们认为如果 active_rows 为 0 且表格隐藏，则不允许设置
             if not self.smart_grid.table.isVisible():
                 return False, "工作区为空，请先导入数据或添加内容"

        # 检查列号是否越界
        max_col = self.smart_grid.table.columnCount()
        for col in columns:
            if col > max_col:
                return False, f"列号 {col} 超出当前工作区范围 (最大 {max_col} 列)"
        
        return True, ""

    # ==================== 槽函数 ====================
    
    def _on_import_excel(self):
        """导入 Excel"""
        self.smart_grid.import_from_excel()
    
    def _on_api_settings(self):
        """API 设置"""
        dialog = APISettingsDialog(self.config, self)
        if dialog.exec():
            logger.info("API 设置已更新")
    
    def _on_bold_tool(self):
        """批量加粗工具"""
        from .dialogs.bold_tool import BoldToolDialog
        dialog = BoldToolDialog(self.config, self)
        dialog.exec()
    
    def _on_about(self):
        """关于"""
        from qfluentwidgets import MessageBox
        w = MessageBox(
            "关于 SEO 工作台",
            "SEO 智能内容工作台 v1.0\n\n"
            "一个专为 SEO 团队设计的内容生产工具\n\n"
            "基于 PyQt-Fluent-Widgets 构建",
            self
        )
        w.yesButton.setText("确定")
        w.cancelButton.hide()
        w.exec()
    
    def _on_generate(self, mode: str):
        """生成文档"""
        logger.info(f"开始生成文档: 模式={mode}")
        from qfluentwidgets import InfoBar, InfoBarPosition
        from PyQt6.QtWidgets import QApplication, QFileDialog
        
        # 获取工作区数据
        grid_data = self.smart_grid.get_grid_data()
        if not grid_data:
            InfoBar.warning(
                title='提示',
                content='工作区为空，请先导入数据或添加内容',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self
            )
            return
        
        # 选择保存路径
        save_dir = QFileDialog.getExistingDirectory(
            self,
            "选择保存目录",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if not save_dir:
            return
        
        # 获取生成数量
        count = self.toolbar.count_spin.value() if mode == "shuffle" else len(grid_data)
        
        # 显示加载状态
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        InfoBar.info(
            title='开始生成',
            content=f"正在生成 {count} 个文档（{mode}模式）...",
            orient=Qt.Orientation.Horizontal,
            isClosable=False,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=3000,
            parent=self
        )
        
        try:
            # 调用生成逻辑
            generated_count = self._generate_documents(grid_data, save_dir, mode, count)
            
            QApplication.restoreOverrideCursor()
            
            InfoBar.success(
                title='生成完成',
                content=f'已生成 {generated_count} 个文档到 {save_dir}',
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self
            )
            
        except Exception as e:
            QApplication.restoreOverrideCursor()
            logger.error(f"生成文档失败: {e}", exc_info=True)
            
            InfoBar.error(
                title='生成失败',
                content=f'错误: {str(e)}',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=5000,
                parent=self
            )
    
    def _generate_documents(self, grid_data: list, save_dir: str, mode: str, count: int) -> int:
        """实际生成文档的逻辑"""
        import random
        from pathlib import Path
        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.oxml.ns import qn
        from datetime import datetime
        from ..core.quality_checker import QualityChecker, QualityReport
        from ..core.smart_numbering import SmartNumbering
        
        generated = 0
        
        # 初始化质量检查器和报告
        quality_checker = None
        quality_report = None
        
        if self.config.quality_check_enabled:
            quality_checker = QualityChecker(
                threshold_premium=self.config.quality_threshold_premium,
                threshold_standard=self.config.quality_threshold_standard,
                seo_keywords=self.config.target_keywords if self.config.seo_check_enabled else [],
                seo_density_min=self.config.seo_density_min,
                seo_density_max=self.config.seo_density_max
            )
            quality_report = QualityReport()
            logger.info("质量检查已启用")
            if self.config.seo_check_enabled and self.config.target_keywords:
                logger.info(f"SEO 密度检查已启用，目标关键词: {self.config.target_keywords}")
        
        if mode == "row":
            # 按行生成模式：每行生成一个文档
            for idx, row_data in enumerate(grid_data):
                doc = Document()
                
                # === 智能序号处理：按写入顺序编号 ===
                global_list_counter = 1
                
                # 根据列类型设置样式
                for col_idx, content in enumerate(row_data):
                    if not content or not content.strip():
                        continue
                    
                    col_type = self.config.get_column_type(col_idx)
                    
                    if col_type == 'Ignore':
                        continue
                    
                    # === 智能序号处理 ===
                    # 将内容按换行符分割成多个段落
                    paragraphs = content.split('\n')
                    
                    # 处理该列的每个段落
                    for para_text in paragraphs:
                        if not para_text.strip():
                            continue
                        
                        processed_content = para_text
                        
                        # === 对所有类型应用智能序号处理 ===
                        if col_type == 'List':
                            # List 类型：检测、清洗并重新编号（按写入顺序）
                            current_number = global_list_counter
                            processed_content = SmartNumbering.process_text(
                                para_text, 
                                current_number,
                                should_renumber=True
                            )
                            logger.info(f"[List] 重编号: {current_number}, 原文='{para_text[:40]}', 结果='{processed_content[:40]}'")
                            global_list_counter += 1
                        elif col_type in ['H1', 'H2', 'H3', 'H4', 'Body']:
                            # 其他类型：检测、清洗并重新编号（按写入顺序）
                            current_number = global_list_counter
                            processed_content = SmartNumbering.process_text(
                                para_text,
                                current_number,
                                should_renumber=True
                            )
                            logger.info(f"[{col_type}] 重编号: {current_number}, 原文='{para_text[:40]}', 结果='{processed_content[:40]}'")
                            global_list_counter += 1
                        
                        # 根据类型添加段落
                        if col_type == 'H1':
                            p = doc.add_paragraph(processed_content)
                            self._apply_heading_style(p, level=1)
                        elif col_type == 'H2':
                            p = doc.add_paragraph(processed_content)
                            self._apply_heading_style(p, level=2)
                        elif col_type == 'H3':
                            p = doc.add_paragraph(processed_content)
                            self._apply_heading_style(p, level=3)
                        elif col_type == 'H4':
                            p = doc.add_paragraph(processed_content)
                            self._apply_heading_style(p, level=4)
                        elif col_type == 'List':
                            p = doc.add_paragraph(processed_content, style='List Bullet')
                            self._apply_body_style(p)
                        elif col_type == 'Body':
                            p = doc.add_paragraph(processed_content)
                            self._apply_body_style(p)
                        
                        # 应用加粗关键词
                        if col_type in ['Body', 'List'] and self.config.bold_keywords:
                            self._apply_bold_keywords(p, self.config.bold_keywords)
                    
                    # 插入该列的图片（如果有）- 在该列所有段落之后
                    self._insert_column_image(doc, col_idx)
                
                # 质量检查和文件名标记
                title = row_data[0] if row_data else f"文档{idx + 1}"
                quality_prefix = ""
                
                if quality_checker:
                    # 创建文档指纹
                    fingerprint = quality_checker.create_fingerprint(row_data)
                    # 提取完整文本用于 SEO 检查
                    full_text = "\n".join([str(content) for content in row_data if content])
                    # 检查质量
                    score = quality_checker.check_quality(fingerprint, full_text)
                    # 添加前缀
                    quality_prefix = f"[{score.rating}]_"
                    # 记录到报告
                    if quality_report:
                        quality_report.add_record(
                            filename=f"{quality_prefix}文档_{idx + 1:04d}.docx",
                            title=title[:50],  # 限制长度
                            max_similarity=score.max_similarity,
                            rating=score.rating,
                            timestamp=datetime.now(),
                            keyword_density=score.keyword_density,
                            density_rating=score.density_rating,
                            seo_suggestion=score.seo_suggestion
                        )
                
                # 保存文档
                filename = f"{quality_prefix}文档_{idx + 1:04d}.docx"
                filepath = Path(save_dir) / filename
                doc.save(str(filepath))
                generated += 1
                
                logger.info(f"已生成文档 {generated}/{len(grid_data)}: {filename}")
                
        else:
            # 随机混排模式：应用混排策略
            # 检查是否启用了标题驱动模式
            use_ai_titles = len(self.ai_title_queue) > 0
            
            for i in range(count):
                doc = Document()
                
                # 随机选择一行作为基础
                base_row_idx = random.randint(0, len(grid_data) - 1)
                
                # 应用混排策略生成新行
                processed_row = self._apply_shuffling_strategies(grid_data, base_row_idx)
                
                # 标题驱动逻辑：如果有 AI 标题队列，替换第一列内容
                if use_ai_titles and i < len(self.ai_title_queue):
                    ai_title = self.ai_title_queue[i]
                    # 将 AI 标题插入到第一列
                    if len(processed_row) > 0:
                        processed_row[0] = ai_title
                    else:
                        processed_row = [ai_title]
                    
                    # 设置第一列的格式为 AI 指定的格式
                    self.config.set_column_type(0, self.ai_title_format, "AI标题")
                    logger.info(f"文档 {i+1}: 使用 AI 标题 '{ai_title}' (格式: {self.ai_title_format})")
                
                # === 智能序号处理：在混排策略之后，写入Word之前 ===
                # 使用全局计数器，按写入顺序编号（不按列索引）
                global_list_counter = 1
                
                # 处理每一列的内容
                for col_idx, content in enumerate(processed_row):
                    if not content or not content.strip():
                        continue
                    
                    col_type = self.config.get_column_type(col_idx)
                    
                    if col_type == 'Ignore':
                        continue
                    
                    # === 智能序号处理 ===
                    # 将内容按换行符分割成多个段落
                    paragraphs = content.split('\n')
                    
                    # 处理该列的每个段落
                    for para_text in paragraphs:
                        if not para_text.strip():
                            continue
                        
                        processed_content = para_text
                        
                        # === 对所有类型应用智能序号处理 ===
                        if col_type == 'List':
                            # List 类型：检测、清洗并重新编号（按写入顺序）
                            current_number = global_list_counter
                            processed_content = SmartNumbering.process_text(
                                para_text, 
                                current_number,  # 使用全局计数器
                                should_renumber=True
                            )
                            logger.info(f"[List] 重编号: {current_number}, 原文='{para_text[:40]}', 结果='{processed_content[:40]}'")
                            global_list_counter += 1  # 每处理一个List段落，全局计数器递增
                        elif col_type in ['H1', 'H2', 'H3', 'H4', 'Body']:
                            # 其他类型：检测、清洗并重新编号（按写入顺序）
                            current_number = global_list_counter
                            processed_content = SmartNumbering.process_text(
                                para_text,
                                current_number,
                                should_renumber=True
                            )
                            logger.info(f"[{col_type}] 重编号: {current_number}, 原文='{para_text[:40]}', 结果='{processed_content[:40]}'")
                            global_list_counter += 1
                        
                        # 根据类型添加段落
                        if col_type == 'H1':
                            p = doc.add_paragraph(processed_content)
                            self._apply_heading_style(p, level=1)
                        elif col_type == 'H2':
                            p = doc.add_paragraph(processed_content)
                            self._apply_heading_style(p, level=2)
                        elif col_type == 'H3':
                            p = doc.add_paragraph(processed_content)
                            self._apply_heading_style(p, level=3)
                        elif col_type == 'H4':
                            p = doc.add_paragraph(processed_content)
                            self._apply_heading_style(p, level=4)
                        elif col_type == 'List':
                            p = doc.add_paragraph(processed_content, style='List Bullet')
                            self._apply_body_style(p)
                        elif col_type == 'Body':
                            p = doc.add_paragraph(processed_content)
                            self._apply_body_style(p)
                        
                        # 应用加粗关键词
                        if col_type in ['Body', 'List'] and self.config.bold_keywords:
                            self._apply_bold_keywords(p, self.config.bold_keywords)
                    
                    # 插入该列的图片（如果有）- 在该列所有段落之后
                    self._insert_column_image(doc, col_idx)
                
                # 质量检查和文件名标记
                title = processed_row[0] if processed_row else f"文档{i + 1}"
                quality_prefix = ""
                
                if quality_checker:
                    # 创建文档指纹
                    fingerprint = quality_checker.create_fingerprint(processed_row)
                    # 提取完整文本用于 SEO 检查
                    full_text = "\n".join([str(content) for content in processed_row if content])
                    # 检查质量
                    score = quality_checker.check_quality(fingerprint, full_text)
                    # 添加前缀
                    quality_prefix = f"[{score.rating}]_"
                    # 记录到报告
                    if quality_report:
                        quality_report.add_record(
                            filename=f"{quality_prefix}{'AI标题文档' if use_ai_titles else '混排文档'}_{i + 1:04d}.docx",
                            title=title[:50],  # 限制长度
                            max_similarity=score.max_similarity,
                            rating=score.rating,
                            timestamp=datetime.now(),
                            keyword_density=score.keyword_density,
                            density_rating=score.density_rating,
                            seo_suggestion=score.seo_suggestion
                        )
                
                # 保存文档
                if use_ai_titles:
                    filename = f"{quality_prefix}AI标题文档_{i + 1:04d}.docx"
                else:
                    filename = f"{quality_prefix}混排文档_{i + 1:04d}.docx"
                filepath = Path(save_dir) / filename
                doc.save(str(filepath))
                generated += 1
                
                logger.info(f"已生成文档 {generated}/{count}: {filename}")
            
            # 生成完成后清空标题队列
            if use_ai_titles:
                self.ai_title_queue = []
                logger.info("AI 标题队列已清空")
        
        # 生成质量报告
        if quality_report and self.config.quality_generate_report:
            report_path = Path(save_dir) / "quality_report.csv"
            quality_report.save_to_csv(str(report_path))
            
            # 统计信息
            stats = quality_report.get_statistics()
            logger.info(f"查重统计: 优质={stats['查重_优质']}, 中等={stats['查重_中等']}, 高重复={stats['查重_高重复']}")
            if self.config.seo_check_enabled and self.config.target_keywords:
                logger.info(f"SEO统计: 完美={stats['SEO_完美']}, 不足={stats['SEO_不足']}, 堆砌={stats['SEO_堆砌']}")
        
        return generated
    
    def _insert_column_image(self, doc, col_idx: int):
        """为指定列插入随机图片
        
        Args:
            doc: Document对象
            col_idx: 列索引
        """
        import random
        from pathlib import Path
        from docx.shared import Inches, Cm
        from PIL import Image
        
        # 检查该列是否有图片组
        if col_idx not in self.config.column_images:
            return
        
        image_paths = self.config.column_images[col_idx]
        if not image_paths:
            return
        
        # 随机选择一张图片
        img_path = random.choice(image_paths)
        img_file = Path(img_path)
        
        if not img_file.exists():
            logger.warning(f"图片文件不存在: {img_path}")
            return
        
        try:
            # 添加图片段落
            paragraph = doc.add_paragraph()
            paragraph.alignment = 1  # 居中对齐
            run = paragraph.add_run()
            
            # 获取图片原始尺寸
            with Image.open(str(img_file)) as img:
                img_width, img_height = img.size
                aspect_ratio = img_height / img_width
            
            # Word A4 文档可用宽度约为 16cm（左右边距各2.54cm，总宽21cm）
            # 设置图片宽度为可用宽度的 90%，即 14.4cm
            max_width = Cm(14.4)
            
            # 插入图片，自动按比例调整高度
            picture = run.add_picture(str(img_file), width=max_width)
            
            # 提取文件名（去掉后缀）作为 Alt Text
            alt_text = img_file.stem  # 自动去掉扩展名
            
            # 设置图片的 Alt Text（替代文本）
            # 这是 SEO 的关键部分
            # 修正：使用 ._inline 而不是 .inline
            inline = picture._inline 
            docPr = inline.docPr
            docPr.set('descr', alt_text)  # 设置描述（Alt Text）
            docPr.set('title', alt_text)  # 同时设置标题
            
            logger.info(f"列 {col_idx+1} 插入图片: {img_file.name}, Alt Text: {alt_text}, 宽度: 14.4cm")
            
        except Exception as e:
            logger.error(f"插入图片失败: {img_path}, 错误: {e}")
    
    def _apply_heading_style(self, paragraph, level: int):
        """应用标题样式
        
        Args:
            paragraph: 段落对象
            level: 标题级别 (1-4)
        """
        from docx.shared import Pt, RGBColor
        from docx.oxml.ns import qn
        
        # 字号映射（中国公文标准）
        font_sizes = {
            1: 24,  # 小一号
            2: 18,  # 小二号
            3: 16,  # 小三号
            4: 14   # 四号
        }
        
        font_size = font_sizes.get(level, 16)
        
        # 设置段落格式
        paragraph_format = paragraph.paragraph_format
        paragraph_format.line_spacing = 1.5  # 1.5倍行距
        paragraph_format.space_after = Pt(10)  # 段后10pt
        
        # 如果段落为空，添加一个run
        if not paragraph.runs:
            paragraph.add_run()
        
        # 对每个run应用样式
        for run in paragraph.runs:
            # 设置字体
            run.font.name = 'Microsoft YaHei'
            run.font.size = Pt(font_size)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0, 0, 0)  # 黑色
            
            # 强制设置中文字体（核心修复）
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    
    def _apply_body_style(self, paragraph):
        """应用正文样式"""
        from docx.shared import Pt, RGBColor
        from docx.oxml.ns import qn
        
        # 设置段落格式
        paragraph_format = paragraph.paragraph_format
        paragraph_format.line_spacing = 1.5  # 1.5倍行距
        paragraph_format.space_after = Pt(10)  # 段后10pt
        
        # 如果段落为空，添加一个run
        if not paragraph.runs:
            paragraph.add_run()
        
        # 对每个run应用样式
        for run in paragraph.runs:
            # 设置字体
            run.font.name = 'Microsoft YaHei'
            run.font.size = Pt(12)  # 小四号
            run.font.bold = False
            run.font.color.rgb = RGBColor(0, 0, 0)  # 黑色
            
            # 强制设置中文字体（核心修复）
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    
    def _apply_shuffling_strategies(self, grid_data: list, base_row_idx: int) -> list:
        """应用混排策略，生成新的行数据"""
        import random
        import copy
        
        # 获取基础行
        base_row = list(grid_data[base_row_idx])
        result_row = copy.deepcopy(base_row)
        
        # 如果没有配置策略，直接返回基础行
        if not self.config.shuffling_strategies:
            return result_row
        
        # 应用每个策略
        for strategy in self.config.shuffling_strategies:
            result_row = self._apply_single_strategy(grid_data, result_row, strategy)
        
        return result_row
    
    def _apply_single_strategy(self, grid_data: list, current_row: list, strategy) -> list:
        """应用单个混排策略
        
        逻辑说明：
        1. 将指定的列按group_size分组
        2. 随机选择keep_count个组保留
        3. 未被选中的组对应的列删除（设为空）
        4. 如果shuffle_order=True，打乱保留的组之间的位置顺序
        """
        import random
        import copy
        
        result_row = copy.deepcopy(current_row)
        
        # 将列索引转换为0-based（策略中是1-based）
        columns = [col - 1 for col in strategy.columns if col > 0]
        
        # 验证列索引是否在范围内
        valid_columns = [col for col in columns if col < len(current_row)]
        if not valid_columns:
            logger.warning(f"策略 '{strategy.name}' 的列索引超出范围，跳过")
            return result_row
        
        # 分组
        groups = []
        for i in range(0, len(valid_columns), strategy.group_size):
            group = valid_columns[i:i + strategy.group_size]
            if len(group) == strategy.group_size:  # 只保留完整的组
                groups.append(group)
        
        if not groups:
            logger.warning(f"策略 '{strategy.name}' 无法形成完整分组，跳过")
            return result_row
        
        # 随机选择指定数量的组（保留的组）
        keep_count = min(strategy.keep_count, len(groups))
        selected_groups = random.sample(groups, keep_count)
        
        # 记录原始组的位置和内容
        original_positions = []  # [(组位置, 组列索引)]
        for group in selected_groups:
            original_positions.append(group)
        
        # 如果需要打乱保留组之间的顺序
        if strategy.shuffle_order:
            # 保存选中组的内容
            group_contents = []
            for group in selected_groups:
                content = [result_row[col_idx] for col_idx in group]
                group_contents.append(content)
            
            # 打乱内容顺序
            random.shuffle(group_contents)
            
            # 将打乱后的内容重新分配到原来的组位置
            for group_idx, group in enumerate(selected_groups):
                for col_idx_in_group, col_idx in enumerate(group):
                    result_row[col_idx] = group_contents[group_idx][col_idx_in_group]
        
        # 收集所有涉及策略的列索引
        all_strategy_columns = set(valid_columns)
        
        # 收集要保留的列索引
        keep_columns = set()
        for group in selected_groups:
            keep_columns.update(group)
        
        # 找出要删除的列（在策略范围内但未被选中的列）
        columns_to_remove = all_strategy_columns - keep_columns
        
        # 将要删除的列设置为空字符串
        for col_idx in columns_to_remove:
            result_row[col_idx] = ""
        
        logger.debug(f"应用策略 '{strategy.name}': "
                    f"总共 {len(groups)} 组, 保留 {keep_count} 组, "
                    f"删除 {len(columns_to_remove)} 列, "
                    f"打乱顺序: {strategy.shuffle_order}")
        
        return result_row
    
    def _apply_bold_keywords(self, paragraph, keywords: list):
        """应用加粗关键词
        
        Args:
            paragraph: 段落对象
            keywords: 关键词列表
        """
        from docx.shared import Pt, RGBColor
        from docx.oxml.ns import qn
        
        if not keywords or not paragraph.text:
            return
        
        # 获取原始文本
        original_text = paragraph.text
        
        # 清空段落的所有runs
        for run in paragraph.runs:
            run.text = ''
        
        # 重新构建段落，对关键词加粗
        current_pos = 0
        text_length = len(original_text)
        
        while current_pos < text_length:
            # 查找最近的关键词
            nearest_keyword = None
            nearest_pos = text_length
            
            for keyword in keywords:
                pos = original_text.find(keyword, current_pos)
                if pos != -1 and pos < nearest_pos:
                    nearest_pos = pos
                    nearest_keyword = keyword
            
            if nearest_keyword:
                # 添加关键词之前的普通文本
                if nearest_pos > current_pos:
                    run = paragraph.add_run(original_text[current_pos:nearest_pos])
                    run.font.name = 'Microsoft YaHei'
                    run.font.size = Pt(12)
                    run.font.color.rgb = RGBColor(0, 0, 0)
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
                
                # 添加加粗的关键词
                run = paragraph.add_run(nearest_keyword)
                run.font.name = 'Microsoft YaHei'
                run.font.size = Pt(12)
                run.font.bold = True
                run.font.color.rgb = RGBColor(0, 0, 0)
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
                
                current_pos = nearest_pos + len(nearest_keyword)
            else:
                # 添加剩余的普通文本
                run = paragraph.add_run(original_text[current_pos:])
                run.font.name = 'Microsoft YaHei'
                run.font.size = Pt(12)
                run.font.color.rgb = RGBColor(0, 0, 0)
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
                break
    
    def _on_generate_complete(self, save_dir: str):
        """生成完成（废弃，已整合到 _on_generate 中）"""
        pass
    
    def _on_ai_title_dialog(self):
        """打开 AI 标题生成对话框"""
        dialog = AITitleDialog(self.config, self)
        if dialog.exec():
            # 用户点击了"确认并使用"
            titles = dialog.get_titles()
            title_format = dialog.get_title_format()
            
            if not titles:
                return
            
            # 保存到标题队列
            self.ai_title_queue = titles
            self.ai_title_format = title_format
            
            # 强制设置生成数量为标题数量
            self.toolbar.count_spin.setValue(len(titles))
            
            # 强制切换到"随机混排"模式
            self.toolbar.mode_combo.setCurrentIndex(1)
            
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.success(
                title='标题已就绪',
                content=f'已加载 {len(titles)} 个标题，请点击"开始生成 Word"',
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self
            )
            
            logger.info(f"AI 标题队列已设置: {len(titles)} 个标题，格式: {title_format}")
    
    def _on_strategy_config(self):
        """打开混排策略配置对话框"""
        dialog = StrategyConfigDialog(self.config, self._validate_strategy_columns, self)
        if dialog.exec():
            # 用户点击了"保存生效"
            # 配置已在对话框中保存，这里只需要刷新界面
            self.strategy_panel._update_strategy_count()
            
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.success(
                title='配置已更新',
                content=f'混排策略配置已生效',
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self
            )
            
            logger.info("混排策略配置已更新")
    
    def _on_seo_config(self):
        """打开 SEO 核心词配置对话框"""
        dialog = SEOSettingDialog(self.config, self)
        if dialog.exec():
            # 用户点击了"保存并生效"
            # 配置已在对话框中保存，这里只需要刷新界面
            self.strategy_panel.update_seo_status()
            
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.success(
                title='配置已更新',
                content=f'SEO 核心词配置已生效',
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self
            )
            
            logger.info(f"SEO 核心词配置已更新: {self.config.target_keywords}")
    
    def _on_ai_title(self, keyword: str, prompt: str):
        """AI 生成标题"""
        logger.info(f"AI 生成标题: keyword={keyword}, prompt={prompt}")
        from qfluentwidgets import InfoBar, InfoBarPosition
        from PyQt6.QtWidgets import QApplication, QTableWidgetItem
        from ..ai.api_client import AIClient
        
        # 检查 API 配置
        if not self.config.api_config.api_key:
            InfoBar.error(
                title='配置错误',
                content='请先在设置中配置 API Key',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self
            )
            return
        
        # 显示加载状态
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        row_count = self.smart_grid.get_active_row_count()
        if row_count == 0:
            row_count = max(1, self.smart_grid.table.rowCount())
        
        InfoBar.info(
            title='AI 助手',
            content=f"正在为 '{keyword}' 生成 {row_count} 个标题...",
            orient=Qt.Orientation.Horizontal,
            isClosable=False,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=2000,
            parent=self
        )
        
        try:
            # 初始化 AI 客户端
            ai_client = AIClient(self.config.api_config)
            
            # 调用 AI 生成标题
            titles = ai_client.generate_titles(
                keyword=keyword,
                count=row_count,
                custom_prompt=prompt if prompt else ""
            )
            
            if not titles:
                QApplication.restoreOverrideCursor()
                InfoBar.error(
                    title='生成失败',
                    content='AI 未返回任何标题，请检查网络或 API 配置',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=3000,
                    parent=self
                )
                return
            
            # 确保表格有足够的行和列
            if self.smart_grid.table.columnCount() == 0:
                self.smart_grid.table.setColumnCount(1)
                self.smart_grid._setup_headers()
            if self.smart_grid.table.rowCount() < len(titles):
                self.smart_grid.table.setRowCount(len(titles))
            
            # 填充标题到第一列
            for i, title in enumerate(titles):
                self.smart_grid.table.setItem(i, 0, QTableWidgetItem(title))
            
            self.smart_grid.empty_hint.hide()
            self.smart_grid.table.show()
            self.smart_grid._update_column_control_positions()
            
            # 恢复光标
            QApplication.restoreOverrideCursor()
            
            InfoBar.success(
                title='生成完成',
                content=f'已生成 {len(titles)} 个标题并导入到第一列',
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self
            )
            
            logger.info(f"AI 标题已导入工作区: {len(titles)} 个")
            
        except Exception as e:
            QApplication.restoreOverrideCursor()
            logger.error(f"AI 生成标题失败: {e}")
            InfoBar.error(
                title='生成失败',
                content=f'错误: {str(e)}',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=5000,
                parent=self
            )
    
    def _on_material_selected(self, material_id: int):
        """素材被选中"""
        logger.debug(f"素材被选中: ID={material_id}")
    
    def _on_grid_data_changed(self):
        """网格数据变化"""
        pass
