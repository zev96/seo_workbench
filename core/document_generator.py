"""
Word 文档生成引擎
核心功能：将网格数据转换为格式化的 Word 文档
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from loguru import logger

from .spintax_parser import SpintaxParser
from .image_processor import ImageProcessor
from .shuffle_engine import ShuffleEngine
from ..config.settings import ProfileConfig
from ..utils.file_handler import FileHandler


class DocumentGenerator:
    """Word 文档生成器"""
    
    def __init__(self, config: ProfileConfig):
        """
        初始化文档生成器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.spintax_parser = SpintaxParser()
        self.image_processor = ImageProcessor()
        
        # 初始化混排引擎
        if config.shuffling_strategies:
            self.shuffle_engine = ShuffleEngine(config.shuffling_strategies)
        else:
            self.shuffle_engine = None
    
    def generate_by_row(
        self,
        grid_data: List[List[str]],
        output_dir: str = "output"
    ) -> List[str]:
        """
        按行生成模式：每行数据生成一个文档
        
        Args:
            grid_data: 网格数据（二维列表）
            output_dir: 输出目录
            
        Returns:
            生成的文件路径列表
        """
        FileHandler.ensure_directory(output_dir)
        generated_files = []
        
        for row_idx, row_data in enumerate(grid_data):
            try:
                # 创建文档
                doc = self._create_document()
                
                # 添加内容
                self._add_row_content(doc, row_data, row_idx)
                
                # 生成文件名
                filename = self._generate_filename(row_data, row_idx)
                filepath = os.path.join(output_dir, filename)
                
                # 保存文档
                if FileHandler.save_word(doc, filepath):
                    generated_files.append(filepath)
                    logger.info(f"生成文档 {row_idx + 1}/{len(grid_data)}: {filename}")
                
            except Exception as e:
                logger.error(f"生成第 {row_idx + 1} 行文档失败: {e}")
        
        logger.info(f"按行生成完成，共 {len(generated_files)} 个文档")
        return generated_files
    
    def generate_by_shuffle(
        self,
        grid_data: List[List[str]],
        count: int,
        output_dir: str = "output"
    ) -> List[str]:
        """
        随机混排模式：随机组合生成指定数量的文档
        
        Args:
            grid_data: 网格数据（二维列表）
            count: 生成数量
            output_dir: 输出目录
            
        Returns:
            生成的文件路径列表
        """
        FileHandler.ensure_directory(output_dir)
        generated_files = []
        
        # 转置数据（按列组织）
        columns_data = self._transpose_grid(grid_data)
        total_columns = len(columns_data)
        
        for doc_idx in range(count):
            try:
                # 创建文档
                doc = self._create_document()
                
                # 随机选择每列的一行
                selected_row = []
                for col_data in columns_data:
                    if col_data:
                        selected_row.append(col_data[doc_idx % len(col_data)])
                    else:
                        selected_row.append("")
                
                # 应用混排策略
                if self.shuffle_engine:
                    keep_map = self.shuffle_engine.execute(total_columns)
                    selected_row = [
                        cell if keep_map.get(i, True) else ""
                        for i, cell in enumerate(selected_row)
                    ]
                
                # 添加内容
                self._add_row_content(doc, selected_row, doc_idx)
                
                # 生成文件名
                filename = self._generate_filename(selected_row, doc_idx)
                filepath = os.path.join(output_dir, filename)
                
                # 保存文档
                if FileHandler.save_word(doc, filepath):
                    generated_files.append(filepath)
                    logger.info(f"生成文档 {doc_idx + 1}/{count}: {filename}")
                
            except Exception as e:
                logger.error(f"生成第 {doc_idx + 1} 个文档失败: {e}")
        
        logger.info(f"混排生成完成，共 {len(generated_files)} 个文档")
        return generated_files
    
    def _create_document(self) -> Document:
        """
        创建 Word 文档（基于模板或空白）
        
        Returns:
            Document 对象
        """
        template_path = self.config.template_path
        return FileHandler.create_word_from_template(template_path)
    
    def _add_row_content(self, doc: Document, row_data: List[str], row_idx: int):
        """
        将一行数据添加到文档
        
        Args:
            doc: Document 对象
            row_data: 行数据
            row_idx: 行索引
        """
        for col_idx, cell_content in enumerate(row_data):
            if not cell_content or not cell_content.strip():
                continue
            
            # 获取列类型
            col_type = self.config.get_column_type(col_idx)
            
            # 忽略此列
            if col_type == 'Ignore':
                continue
            
            # 解析 Spintax
            parsed_content = self.spintax_parser.parse(cell_content)
            
            # 根据类型添加内容
            if col_type == 'H1':
                self._add_heading(doc, parsed_content, level=1)
            elif col_type == 'H2':
                self._add_heading(doc, parsed_content, level=2)
            elif col_type == 'H3':
                self._add_heading(doc, parsed_content, level=3)
            elif col_type == 'List':
                self._add_list_item(doc, parsed_content)
            else:  # Body
                self._add_paragraph(doc, parsed_content)
            
            # 插入图片（如果该列绑定了图片文件夹）
            image_path = self.config.get_image_path(col_idx)
            if image_path:
                self._add_image(doc, image_path, row_idx)
    
    def _add_heading(self, doc: Document, text: str, level: int):
        """
        添加标题
        
        Args:
            doc: Document 对象
            text: 文本内容
            level: 标题级别（1-3）
        """
        heading = doc.add_heading(text, level=level)
        self._apply_chinese_font(heading)
    
    def _add_paragraph(self, doc: Document, text: str):
        """
        添加段落
        
        Args:
            doc: Document 对象
            text: 文本内容
        """
        paragraph = doc.add_paragraph(text)
        self._apply_chinese_font(paragraph)
        self._apply_bold_keywords(paragraph)
        
        # 设置行间距和段后间距
        paragraph.paragraph_format.line_spacing = 1.5
        paragraph.paragraph_format.space_after = Pt(10)
    
    def _add_list_item(self, doc: Document, text: str):
        """
        添加列表项
        
        Args:
            doc: Document 对象
            text: 文本内容
        """
        paragraph = doc.add_paragraph(text, style='List Bullet')
        self._apply_chinese_font(paragraph)
    
    def _add_image(self, doc: Document, image_folder: str, index: int):
        """
        添加图片
        
        Args:
            doc: Document 对象
            image_folder: 图片文件夹路径
            index: 索引（用于循环选择）
        """
        try:
            # 获取图片列表
            image_files = FileHandler.get_image_files(image_folder)
            if not image_files:
                logger.warning(f"图片文件夹为空: {image_folder}")
                return
            
            # 循环获取图片
            image_path = self.image_processor.get_cyclic_image(image_files, index)
            if not image_path:
                return
            
            # 获取 Alt 文本
            alt_text = self.image_processor.get_image_alt_text(image_path)
            
            # 插入图片
            paragraph = doc.add_paragraph()
            run = paragraph.add_run()
            picture = run.add_picture(image_path, width=Inches(5))
            
            # 设置 Alt 文本
            picture._element.attrib['descr'] = alt_text
            
            # 居中对齐
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            logger.debug(f"插入图片: {alt_text}")
            
        except Exception as e:
            logger.error(f"插入图片失败: {e}")
    
    def _apply_chinese_font(self, paragraph):
        """
        应用中文字体（修复 python-docx 中文显示问题）
        
        Args:
            paragraph: 段落对象
        """
        for run in paragraph.runs:
            run.font.name = 'Microsoft YaHei'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    
    def _apply_bold_keywords(self, paragraph):
        """
        对关键词加粗
        
        Args:
            paragraph: 段落对象
        """
        keywords = self.config.bold_keywords
        if not keywords:
            return
        
        for run in paragraph.runs:
            for keyword in keywords:
                if keyword in run.text:
                    run.font.bold = True
                    break
    
    def _generate_filename(self, row_data: List[str], index: int) -> str:
        """
        生成文件名
        
        Args:
            row_data: 行数据
            index: 索引
            
        Returns:
            文件名
        """
        # 尝试使用第一列（通常是标题）作为文件名
        if row_data and row_data[0]:
            title = row_data[0][:30]  # 限制长度
            # 清理文件名
            from ..utils.validators import sanitize_filename
            filename = sanitize_filename(title)
        else:
            filename = f"document_{index + 1}"
        
        return f"{filename}.docx"
    
    def _transpose_grid(self, grid_data: List[List[str]]) -> List[List[str]]:
        """
        转置网格数据（行列互换）
        
        Args:
            grid_data: 网格数据
            
        Returns:
            转置后的数据
        """
        if not grid_data:
            return []
        
        max_cols = max(len(row) for row in grid_data)
        columns = []
        
        for col_idx in range(max_cols):
            column = []
            for row in grid_data:
                if col_idx < len(row):
                    column.append(row[col_idx])
                else:
                    column.append("")
            columns.append(column)
        
        return columns


if __name__ == "__main__":
    # 测试代码
    from ..utils.logger import setup_logger
    from ..config.settings import create_default_config
    
    setup_logger()
    
    # 创建测试配置
    config = create_default_config()
    config.set_column_type(0, 'H1', '标题')
    config.set_column_type(1, 'Body', '内容')
    
    # 创建生成器
    generator = DocumentGenerator(config)
    
    # 测试数据
    test_data = [
        ["测试标题1", "这是{第一|首个}测试内容"],
        ["测试标题2", "这是{第二|另一个}测试内容"],
    ]
    
    # 按行生成
    files = generator.generate_by_row(test_data, "test_output")
    logger.info(f"生成的文件: {files}")

