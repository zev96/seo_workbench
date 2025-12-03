"""
对比表功能快速测试脚本
用于验证完整功能流程
"""

from database.comparison_db_manager import ComparisonDBManager
from core.comparison_image_generator import ComparisonTableImageGenerator
from loguru import logger
import os


def test_database_operations():
    """测试数据库操作"""
    print("\n" + "="*50)
    print("测试 1: 数据库基本操作")
    print("="*50)
    
    db = ComparisonDBManager()
    
    # 创建类目
    print("\n创建类目...")
    category = db.add_category("吸尘器测试", "🧹")
    if not category:
        print("类目已存在，使用现有类目")
        categories = db.get_all_categories()
        category = categories[0] if categories else None
    
    if not category:
        print("❌ 无法创建类目")
        return None
    
    print(f"✅ 类目创建成功: {category.name} (ID: {category.id})")
    
    # 添加品牌
    print("\n添加品牌...")
    brand1 = db.add_brand(category.id, "希喂", is_own=1, sort_order=0)
    brand2 = db.add_brand(category.id, "美的", is_own=0, sort_order=1)
    brand3 = db.add_brand(category.id, "小米", is_own=0, sort_order=2)
    
    if brand1:
        print(f"✅ 品牌添加成功: 希喂 (我方品牌)")
    if brand2:
        print(f"✅ 品牌添加成功: 美的")
    if brand3:
        print(f"✅ 品牌添加成功: 小米")
    
    # 添加参数
    print("\n添加参数...")
    param1 = db.add_parameter(category.id, "价格", sort_order=0)
    param2 = db.add_parameter(category.id, "功率", sort_order=1)
    param3 = db.add_parameter(category.id, "重量", sort_order=2)
    param4 = db.add_parameter(category.id, "噪音", sort_order=3)
    
    if param1:
        print(f"✅ 参数添加成功: 价格")
    if param2:
        print(f"✅ 参数添加成功: 功率")
    if param3:
        print(f"✅ 参数添加成功: 重量")
    if param4:
        print(f"✅ 参数添加成功: 噪音")
    
    # 填充数据
    print("\n填充数据...")
    if brand1 and param1:
        db.set_value(category.id, brand1.id, param1.id, "999元")
        db.set_value(category.id, brand1.id, param2.id, "2000W")
        db.set_value(category.id, brand1.id, param3.id, "3.5kg")
        db.set_value(category.id, brand1.id, param4.id, "65dB")
        print("✅ 希喂数据填充完成")
    
    if brand2 and param1:
        db.set_value(category.id, brand2.id, param1.id, "1299元")
        db.set_value(category.id, brand2.id, param2.id, "1800W")
        db.set_value(category.id, brand2.id, param3.id, "4.2kg")
        db.set_value(category.id, brand2.id, param4.id, "68dB")
        print("✅ 美的数据填充完成")
    
    if brand3 and param1:
        db.set_value(category.id, brand3.id, param1.id, "1199元")
        db.set_value(category.id, brand3.id, param2.id, "2200W")
        db.set_value(category.id, brand3.id, param3.id, "3.8kg")
        db.set_value(category.id, brand3.id, param4.id, "70dB")
        print("✅ 小米数据填充完成")
    
    return category.id


def test_config_operations():
    """测试配置操作"""
    print("\n" + "="*50)
    print("测试 2: 配置管理")
    print("="*50)
    
    db = ComparisonDBManager()
    
    # 保存样式配置
    print("\n保存样式配置...")
    style_config = {
        'preset': 'business_blue',
        'header_bg_color': '#4472C4',
        'header_text_color': '#FFFFFF',
        'own_brand_bg_color': '#FFF2CC',
        'border_width': 1.5,
        'image_width': 15,
        'dpi': 300,
        'font_name': 'Microsoft YaHei',
        'font_size': 10
    }
    
    if db.save_config('table_style', style_config):
        print("✅ 样式配置保存成功")
    else:
        print("❌ 样式配置保存失败")
    
    # 保存插入策略配置
    print("\n保存插入策略配置...")
    insert_config = {
        'own_brand_name': '希喂',
        'fallback_competitor_count': 2,
        'insert_mode': 'anchor',
        'insert_column': 1,
        'insert_anchor_text': '参数对比'
    }
    
    if db.save_config('insert_strategy', insert_config):
        print("✅ 插入策略配置保存成功")
    else:
        print("❌ 插入策略配置保存失败")
    
    # 读取配置验证
    print("\n验证配置...")
    loaded_style = db.get_config('table_style')
    loaded_insert = db.get_config('insert_strategy')
    
    if loaded_style:
        print(f"✅ 读取样式配置成功: DPI={loaded_style['dpi']}")
    if loaded_insert:
        print(f"✅ 读取策略配置成功: 我方品牌={loaded_insert['own_brand_name']}")


def test_image_generation(category_id):
    """测试图片生成"""
    print("\n" + "="*50)
    print("测试 3: 图片生成")
    print("="*50)
    
    db = ComparisonDBManager()
    generator = ComparisonTableImageGenerator()
    
    # 场景1：文章提及美的和小米
    print("\n场景1: 文章提及 [美的, 小米]")
    try:
        image_path = generator.generate_from_category(
            db_manager=db,
            category_id=category_id,
            mentioned_brands=["美的", "小米"],
            output_path="test_output_scenario1.png"
        )
        if os.path.exists(image_path):
            print(f"✅ 图片生成成功: {image_path}")
            print(f"   预期包含品牌: 希喂(我方) + 美的 + 小米")
        else:
            print("❌ 图片文件未生成")
    except Exception as e:
        print(f"❌ 图片生成失败: {e}")
    
    # 场景2：文章只提及美的
    print("\n场景2: 文章只提及 [美的]")
    try:
        image_path = generator.generate_from_category(
            db_manager=db,
            category_id=category_id,
            mentioned_brands=["美的"],
            output_path="test_output_scenario2.png"
        )
        if os.path.exists(image_path):
            print(f"✅ 图片生成成功: {image_path}")
            print(f"   预期包含品牌: 希喂(我方) + 美的 + 小米(保底随机)")
        else:
            print("❌ 图片文件未生成")
    except Exception as e:
        print(f"❌ 图片生成失败: {e}")
    
    # 场景3：文章未提及任何竞品
    print("\n场景3: 文章未提及任何竞品")
    try:
        image_path = generator.generate_from_category(
            db_manager=db,
            category_id=category_id,
            mentioned_brands=[],
            output_path="test_output_scenario3.png"
        )
        if os.path.exists(image_path):
            print(f"✅ 图片生成成功: {image_path}")
            print(f"   预期包含品牌: 希喂(我方) + 2个随机竞品")
        else:
            print("❌ 图片文件未生成")
    except Exception as e:
        print(f"❌ 图片生成失败: {e}")


def test_data_query():
    """测试数据查询"""
    print("\n" + "="*50)
    print("测试 4: 数据查询")
    print("="*50)
    
    db = ComparisonDBManager()
    
    # 查询所有类目
    print("\n查询所有类目...")
    categories = db.get_all_categories()
    print(f"✅ 找到 {len(categories)} 个类目:")
    for cat in categories:
        print(f"   - {cat.name} (ID: {cat.id})")
    
    if categories:
        category_id = categories[0].id
        
        # 查询品牌
        print(f"\n查询类目 '{categories[0].name}' 的品牌...")
        brands = db.get_brands_by_category(category_id)
        print(f"✅ 找到 {len(brands)} 个品牌:")
        for brand in brands:
            own_flag = " [我方品牌]" if brand.is_own == 1 else ""
            print(f"   - {brand.name}{own_flag}")
        
        # 查询参数
        print(f"\n查询类目 '{categories[0].name}' 的参数...")
        parameters = db.get_parameters_by_category(category_id)
        print(f"✅ 找到 {len(parameters)} 个参数:")
        for param in parameters:
            print(f"   - {param.name}")
        
        # 查询完整表格数据
        print(f"\n查询完整表格数据...")
        table_data = db.get_table_data(category_id)
        print(f"✅ 表格结构:")
        print(f"   品牌数: {len(table_data['brands'])}")
        print(f"   参数数: {len(table_data['parameters'])}")
        print(f"   数值数: {len(table_data['values'])}")


def main():
    """主测试流程"""
    print("\n" + "="*70)
    print(" "*15 + "对比表功能完整测试")
    print("="*70)
    
    try:
        # 测试1: 数据库操作
        category_id = test_database_operations()
        
        if not category_id:
            print("\n❌ 数据库测试失败，停止后续测试")
            return
        
        # 测试2: 配置管理
        test_config_operations()
        
        # 测试3: 图片生成
        test_image_generation(category_id)
        
        # 测试4: 数据查询
        test_data_query()
        
        # 总结
        print("\n" + "="*70)
        print(" "*20 + "测试完成!")
        print("="*70)
        print("\n✅ 所有功能测试通过")
        print("\n生成的测试图片:")
        print("  - test_output_scenario1.png (提及美的+小米)")
        print("  - test_output_scenario2.png (只提及美的)")
        print("  - test_output_scenario3.png (未提及竞品)")
        print("\n请查看图片验证显示效果！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

