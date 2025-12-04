"""
对比表图片生成器
使用 Matplotlib 绘制高清对比表格图片
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rcParams
import numpy as np
from typing import List, Dict, Tuple, Optional
from loguru import logger
import os
import tempfile

class ComparisonTableImageGenerator:
    """对比表图片生成器"""
    
    def __init__(self):
        """初始化生成器"""
        # 设置中文字体
        self._setup_chinese_font()
    def _setup_chinese_font(self):
        """设置中文字体支持"""
        try:
            # 尝试使用系统中文字体
            font_names = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS']
            
            for font_name in font_names:
                try:
                    # 检查字体是否可用
                    font_path = fm.findfont(fm.FontProperties(family=font_name))
                    if font_path and os.path.exists(font_path):
                        rcParams['font.sans-serif'] = [font_name]
                        rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
                        logger.info(f"使用字体: {font_name}")
                        return
                except:
                    continue
            
            logger.warning("未找到中文字体，可能显示乱码")
            
        except Exception as e:
            logger.error(f"设置中文字体失败: {e}")
    
    def _wrap_text(self, text: str, max_chars: int) -> str:
        """
        文本自动换行
        
        Args:
            text: 原始文本
            max_chars: 每行最多字符数
            
        Returns:
            换行后的文本
        """
        if not text or len(text) <= max_chars:
            return text
        
        # 按指定长度分割文本
        lines = []
        current_pos = 0
        text_len = len(text)
        
        while current_pos < text_len:
            # 取一行的文本
            line_end = min(current_pos + max_chars, text_len)
            line = text[current_pos:line_end]
            lines.append(line)
            current_pos = line_end
        
        return '\n'.join(lines)
    
    def generate_table_image(
        self,
        brands: List[Dict],  # [{'id': 1, 'name': '希喂', 'is_own': 1}, ...]
        parameters: List[Dict],  # [{'id': 1, 'name': '价格'}, ...]
        values: Dict[Tuple[int, int], str],  # {(brand_id, param_id): value}
        style_config: Optional[Dict] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        生成对比表格图片
        
        Args:
            brands: 品牌列表
            parameters: 参数列表
            values: 参数值字典
            style_config: 样式配置
            output_path: 输出路径（如果为None则生成临时文件）
        
        Returns:
            生成的图片路径
        """
        try:
            # 默认样式配置
            if style_config is None:
                style_config = {
                    'header_bg_color': '#4472C4',
                    'header_text_color': '#FFFFFF',
                    'own_brand_bg_color': '#FFF2CC',
                    'border_width': 1.5,
                    'image_width': 15,
                    'dpi': 300,
                    'font_name': 'Microsoft YaHei',
                    'font_size': 10
                }
            
            # 设置字体
            if style_config.get('font_name'):
                rcParams['font.sans-serif'] = [style_config['font_name']]
            
            # 准备数据
            num_brands = len(brands)
            num_params = len(parameters)
            
            # 创建数据矩阵（包含表头）
            # 第一行：品牌名
            # 第一列：参数名
            data_matrix = []
            
            # 第一行：表头（参数/品牌 + 各品牌名）
            header_row = ['参数/品牌'] + [b['name'] for b in brands]
            data_matrix.append(header_row)
            
            # 后续行：参数名 + 各参数值
            for param in parameters:
                row = [param['name']]
                for brand in brands:
                    value = values.get((brand['id'], param['id']), '')
                    row.append(value)
                data_matrix.append(row)
            
            # 文本换行处理
            wrapped_data_matrix = []
            max_chars_per_line = 15  # 每行最多字符数
            
            for row in data_matrix:
                wrapped_row = []
                for cell_text in row:
                    # 自动换行
                    wrapped_text = self._wrap_text(str(cell_text), max_chars_per_line)
                    wrapped_row.append(wrapped_text)
                wrapped_data_matrix.append(wrapped_row)
            
            # 计算每行的行数（用于动态行高）
            row_line_counts = []
            for row in wrapped_data_matrix:
                max_lines = max(text.count('\n') + 1 for text in row)
                row_line_counts.append(max_lines)
            
            # 创建图形
            # 动态计算图形尺寸
            cell_width = 2.2  # 每个单元格宽度（英寸）
            base_cell_height = 0.4  # 基础单元格高度（英寸）
            line_height = 0.25  # 每行文本的额外高度
            
            fig_width = (num_brands + 1) * cell_width
            # 根据每行的文本行数计算总高度
            fig_height = sum(base_cell_height + (lines - 1) * line_height for lines in row_line_counts)
            
            fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=style_config['dpi'])
            ax.axis('tight')
            ax.axis('off')
            
            # 创建表格
            table = ax.table(
                cellText=wrapped_data_matrix,
                cellLoc='center',
                loc='center',
                bbox=[0, 0, 1, 1]
            )
            
            # 设置表格样式
            table.auto_set_font_size(False)
            table.set_fontsize(style_config['font_size'])
            
            # 设置单元格样式和动态行高
            total_height = sum(row_line_counts)
            for (row, col), cell in table.get_celld().items():
                # 设置边框
                cell.set_linewidth(style_config['border_width'])
                cell.set_edgecolor('#000000')
                
                # 动态行高（根据该行的文本行数）
                row_height = row_line_counts[row] / total_height
                cell.set_height(row_height)
                
                # 第一行（品牌名）
                if row == 0:
                    cell.set_facecolor(style_config['header_bg_color'])
                    cell.set_text_props(
                        weight='bold',
                        color=style_config['header_text_color']
                    )
                
                # 第一列（参数名）
                elif col == 0:
                    cell.set_facecolor('#F0F0F0')
                    cell.set_text_props(weight='bold')
                
                # 我方品牌列
                elif col > 0 and brands[col - 1].get('is_own') == 1:
                    cell.set_facecolor(style_config['own_brand_bg_color'])
                
                # 普通数据单元格
                else:
                    cell.set_facecolor('#FFFFFF')
            
            # 保存图片
            if output_path is None:
                # 生成临时文件
                temp_dir = tempfile.gettempdir()
                output_path = os.path.join(temp_dir, f'comparison_table_{id(self)}.png')
            
            plt.savefig(
                output_path,
                dpi=style_config['dpi'],
                bbox_inches='tight',
                pad_inches=0.1,
                facecolor='white'
            )
            plt.close(fig)
            
            logger.info(f"对比表图片生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"生成对比表图片失败: {e}")
            raise
    
    def generate_from_category(
        self,
        db_manager,
        category_id: int,
        mentioned_brands: List[str],
        style_config: Optional[Dict] = None,
        insert_config: Optional[Dict] = None,
        output_path: Optional[str] = None,
        selected_parameter_ids: Optional[List[int]] = None
    ) -> str:
        """
        根据类目ID和提及的品牌生成对比表
        
        Args:
            db_manager: 数据库管理器
            category_id: 类目ID
            mentioned_brands: 文章中提及的品牌列表
            style_config: 样式配置
            insert_config: 插入策略配置
            output_path: 输出路径
            selected_parameter_ids: 选中的参数ID列表（None表示全部）
        
        Returns:
            生成的图片路径
        """
        try:
            # 获取表格数据
            table_data = db_manager.get_table_data(category_id)
            all_brands = table_data['brands']
            all_parameters = table_data['parameters']
            values = table_data['values']
            
            # 过滤参数（如果指定了selected_parameter_ids）
            if selected_parameter_ids:
                parameters = [p for p in all_parameters if p['id'] in selected_parameter_ids]
                logger.info(f"参数过滤: 总数={len(all_parameters)}, 选中={len(parameters)}")
            else:
                parameters = all_parameters
                logger.info(f"使用全部参数: {len(parameters)}个")
            
            logger.info(f"数据库中共有 {len(all_brands)} 个品牌")
            logger.info(f"文章中提及的品牌: {mentioned_brands}")
            
            # 默认插入配置
            if insert_config is None:
                insert_config = {
                    'own_brand_name': '希喂',
                    'fallback_competitor_count': 2
                }
            
            # 筛选要显示的品牌
            selected_brands = []
            own_brand = None
            
            # 1. 首先找出我方品牌
            for brand in all_brands:
                if brand['is_own'] == 1:
                    own_brand = brand
                    logger.info(f"找到我方品牌（标记）: {brand['name']}")
                    break
            
            # 如果没有标记我方品牌，尝试按名称查找
            if not own_brand:
                own_brand_name = insert_config['own_brand_name']
                for brand in all_brands:
                    if brand['name'] == own_brand_name:
                        own_brand = brand
                        brand['is_own'] = 1  # 临时标记
                        logger.info(f"找到我方品牌（按名称）: {brand['name']}")
                        break
            
            # 2. 我方品牌永远排第一位
            if own_brand:
                selected_brands.append(own_brand)
                logger.info(f"✓ 我方品牌已加入: {own_brand['name']}")
            else:
                logger.warning(f"未找到我方品牌: {insert_config.get('own_brand_name')}")
            
            # 3. 添加文章中提及的竞品
            competitor_brands = []
            for brand in all_brands:
                if brand['is_own'] != 1 and brand['name'] in mentioned_brands:
                    competitor_brands.append(brand)
                    logger.info(f"✓ 竞品已加入（文章提及）: {brand['name']}")
            
            # 4. 如果竞品不足，随机补充
            fallback_count = insert_config.get('fallback_competitor_count', 2)
            if len(competitor_brands) < fallback_count:
                remaining_brands = [
                    b for b in all_brands 
                    if b['is_own'] != 1 and b not in competitor_brands
                ]
                # 随机选择
                import random
                needed = fallback_count - len(competitor_brands)
                additional = random.sample(
                    remaining_brands,
                    min(needed, len(remaining_brands))
                )
                for brand in additional:
                    logger.info(f"✓ 竞品已加入（保底随机）: {brand['name']}")
                competitor_brands.extend(additional)
            
            selected_brands.extend(competitor_brands)
            
            logger.info(f"最终选择的品牌: {[b['name'] for b in selected_brands]}")
            
            if not selected_brands:
                logger.error("没有可用的品牌数据，无法生成对比表")
                return None
            
            # 生成图片
            return self.generate_table_image(
                brands=selected_brands,
                parameters=parameters,
                values=values,
                style_config=style_config,
                output_path=output_path
            )
            
        except Exception as e:
            logger.error(f"根据类目生成对比表失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise


def test_generator():
    """测试函数"""
    from ..database.comparison_db_manager import ComparisonDBManager
    
    # 创建测试数据
    db_manager = ComparisonDBManager()
    
    # 添加测试类目
    category = db_manager.add_category("吸尘器", "🧹")
    if not category:
        print("类目已存在，使用现有类目")
        categories = db_manager.get_all_categories()
        if categories:
            category_id = categories[0].id
        else:
            print("没有可用类目")
            return
    else:
        category_id = category.id
    
    # 添加品牌
    brand1 = db_manager.add_brand(category_id, "希喂", is_own=1, sort_order=0)
    brand2 = db_manager.add_brand(category_id, "美的", is_own=0, sort_order=1)
    brand3 = db_manager.add_brand(category_id, "小米", is_own=0, sort_order=2)
    
    # 添加参数
    param1 = db_manager.add_parameter(category_id, "价格", sort_order=0)
    param2 = db_manager.add_parameter(category_id, "功率", sort_order=1)
    param3 = db_manager.add_parameter(category_id, "重量", sort_order=2)
    
    # 添加数值
    if brand1 and param1:
        db_manager.set_value(category_id, brand1.id, param1.id, "999元")
        db_manager.set_value(category_id, brand1.id, param2.id, "2000W")
        db_manager.set_value(category_id, brand1.id, param3.id, "3.5kg")
    
    if brand2 and param1:
        db_manager.set_value(category_id, brand2.id, param1.id, "1299元")
        db_manager.set_value(category_id, brand2.id, param2.id, "1800W")
        db_manager.set_value(category_id, brand2.id, param3.id, "4.2kg")
    
    if brand3 and param1:
        db_manager.set_value(category_id, brand3.id, param1.id, "1199元")
        db_manager.set_value(category_id, brand3.id, param2.id, "2200W")
        db_manager.set_value(category_id, brand3.id, param3.id, "3.8kg")
    
    # 生成图片
    generator = ComparisonTableImageGenerator()
    output_path = generator.generate_from_category(
        db_manager=db_manager,
        category_id=category_id,
        mentioned_brands=["美的", "小米"],
        output_path="test_comparison_table.png"
    )
    
    print(f"测试图片已生成: {output_path}")


if __name__ == '__main__':
    test_generator()

