"""
对比表数据库管理类
提供对比表的增删改查接口
"""

from typing import List, Optional, Dict, Tuple
from sqlalchemy import and_
from sqlalchemy.orm import Session
from loguru import logger

from .models import (
    ComparisonCategory, ComparisonBrand, 
    ComparisonParameter, ComparisonValue, ComparisonConfig,
    ComparisonTask, TaskParameterSelection
)
from .db_manager import DatabaseManager


class ComparisonDBManager:
    """对比表数据库管理器"""
    
    def __init__(self):
        """初始化管理器"""
        self.db = DatabaseManager()
        
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.db.get_session()
    
    # ==================== 类目管理 ====================
    
    def add_category(self, name: str, icon: str = None) -> Optional[ComparisonCategory]:
        """
        添加新类目
        
        Args:
            name: 类目名称
            icon: 图标名称
            
        Returns:
            创建的类目对象或None
        """
        session = self.get_session()
        try:
            # 检查是否已存在
            existing = session.query(ComparisonCategory).filter(
                ComparisonCategory.name == name
            ).first()
            
            if existing:
                logger.warning(f"类目已存在: {name}")
                return None
            
            category = ComparisonCategory(name=name, icon=icon)
            session.add(category)
            session.commit()
            session.refresh(category)
            
            logger.info(f"添加类目成功: {name}")
            return category
            
        except Exception as e:
            session.rollback()
            logger.error(f"添加类目失败: {e}")
            return None
        finally:
            session.close()
    
    def delete_category(self, category_id: int) -> bool:
        """删除类目（级联删除相关数据）"""
        session = self.get_session()
        try:
            category = session.query(ComparisonCategory).filter(
                ComparisonCategory.id == category_id
            ).first()
            
            if category:
                session.delete(category)
                session.commit()
                logger.info(f"删除类目成功: ID={category_id}")
                return True
            else:
                logger.warning(f"类目不存在: ID={category_id}")
                return False
                
        except Exception as e:
            session.rollback()
            logger.error(f"删除类目失败: {e}")
            return False
        finally:
            session.close()
    
    def update_category(self, category_id: int, name: str = None, icon: str = None) -> bool:
        """更新类目信息"""
        session = self.get_session()
        try:
            category = session.query(ComparisonCategory).filter(
                ComparisonCategory.id == category_id
            ).first()
            
            if not category:
                logger.warning(f"类目不存在: ID={category_id}")
                return False
            
            if name:
                category.name = name
            if icon is not None:
                category.icon = icon
            
            session.commit()
            logger.info(f"更新类目成功: ID={category_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"更新类目失败: {e}")
            return False
        finally:
            session.close()
    
    def get_all_categories(self) -> List[ComparisonCategory]:
        """获取所有类目"""
        session = self.get_session()
        try:
            return session.query(ComparisonCategory).order_by(
                ComparisonCategory.created_at.desc()
            ).all()
        finally:
            session.close()
    
    def get_category_by_id(self, category_id: int) -> Optional[ComparisonCategory]:
        """根据ID获取类目"""
        session = self.get_session()
        try:
            return session.query(ComparisonCategory).filter(
                ComparisonCategory.id == category_id
            ).first()
        finally:
            session.close()
    
    # ==================== 品牌管理 ====================
    
    def add_brand(self, category_id: int, name: str, is_own: int = 0, sort_order: int = 0) -> Optional[ComparisonBrand]:
        """添加品牌"""
        session = self.get_session()
        try:
            # 检查是否已存在
            existing = session.query(ComparisonBrand).filter(
                and_(
                    ComparisonBrand.category_id == category_id,
                    ComparisonBrand.name == name
                )
            ).first()
            
            if existing:
                logger.warning(f"品牌已存在: {name}")
                return None
            
            brand = ComparisonBrand(
                category_id=category_id,
                name=name,
                is_own=is_own,
                sort_order=sort_order
            )
            session.add(brand)
            session.commit()
            session.refresh(brand)
            
            logger.info(f"添加品牌成功: {name}")
            return brand
            
        except Exception as e:
            session.rollback()
            logger.error(f"添加品牌失败: {e}")
            return None
        finally:
            session.close()
    
    def delete_brand(self, brand_id: int) -> bool:
        """删除品牌"""
        session = self.get_session()
        try:
            brand = session.query(ComparisonBrand).filter(
                ComparisonBrand.id == brand_id
            ).first()
            
            if brand:
                session.delete(brand)
                session.commit()
                logger.info(f"删除品牌成功: ID={brand_id}")
                return True
            return False
            
        except Exception as e:
            session.rollback()
            logger.error(f"删除品牌失败: {e}")
            return False
        finally:
            session.close()
    
    def update_brand(self, brand_id: int, **kwargs) -> bool:
        """更新品牌信息"""
        session = self.get_session()
        try:
            brand = session.query(ComparisonBrand).filter(
                ComparisonBrand.id == brand_id
            ).first()
            
            if not brand:
                return False
            
            for key, value in kwargs.items():
                if hasattr(brand, key):
                    setattr(brand, key, value)
            
            session.commit()
            logger.info(f"更新品牌成功: ID={brand_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"更新品牌失败: {e}")
            return False
        finally:
            session.close()
    
    def get_brands_by_category(self, category_id: int) -> List[ComparisonBrand]:
        """获取类目下的所有品牌"""
        session = self.get_session()
        try:
            return session.query(ComparisonBrand).filter(
                ComparisonBrand.category_id == category_id
            ).order_by(ComparisonBrand.sort_order).all()
        finally:
            session.close()
    
    # ==================== 参数管理 ====================
    
    def add_parameter(self, category_id: int, name: str, sort_order: int = 0) -> Optional[ComparisonParameter]:
        """添加参数"""
        session = self.get_session()
        try:
            # 检查是否已存在
            existing = session.query(ComparisonParameter).filter(
                and_(
                    ComparisonParameter.category_id == category_id,
                    ComparisonParameter.name == name
                )
            ).first()
            
            if existing:
                logger.warning(f"参数已存在: {name}")
                return None
            
            parameter = ComparisonParameter(
                category_id=category_id,
                name=name,
                sort_order=sort_order
            )
            session.add(parameter)
            session.commit()
            session.refresh(parameter)
            
            logger.info(f"添加参数成功: {name}")
            return parameter
            
        except Exception as e:
            session.rollback()
            logger.error(f"添加参数失败: {e}")
            return None
        finally:
            session.close()
    
    def delete_parameter(self, parameter_id: int) -> bool:
        """删除参数"""
        session = self.get_session()
        try:
            parameter = session.query(ComparisonParameter).filter(
                ComparisonParameter.id == parameter_id
            ).first()
            
            if parameter:
                session.delete(parameter)
                session.commit()
                logger.info(f"删除参数成功: ID={parameter_id}")
                return True
            return False
            
        except Exception as e:
            session.rollback()
            logger.error(f"删除参数失败: {e}")
            return False
        finally:
            session.close()
    
    def update_parameter(self, parameter_id: int, **kwargs) -> bool:
        """更新参数信息"""
        session = self.get_session()
        try:
            parameter = session.query(ComparisonParameter).filter(
                ComparisonParameter.id == parameter_id
            ).first()
            
            if not parameter:
                return False
            
            for key, value in kwargs.items():
                if hasattr(parameter, key):
                    setattr(parameter, key, value)
            
            session.commit()
            logger.info(f"更新参数成功: ID={parameter_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"更新参数失败: {e}")
            return False
        finally:
            session.close()
    
    def get_parameters_by_category(self, category_id: int) -> List[ComparisonParameter]:
        """获取类目下的所有参数"""
        session = self.get_session()
        try:
            return session.query(ComparisonParameter).filter(
                ComparisonParameter.category_id == category_id
            ).order_by(ComparisonParameter.sort_order).all()
        finally:
            session.close()
    
    # ==================== 数值管理 ====================
    
    def set_value(self, category_id: int, brand_id: int, parameter_id: int, value: str) -> bool:
        """设置参数值"""
        session = self.get_session()
        try:
            # 查找是否已存在
            existing = session.query(ComparisonValue).filter(
                and_(
                    ComparisonValue.category_id == category_id,
                    ComparisonValue.brand_id == brand_id,
                    ComparisonValue.parameter_id == parameter_id
                )
            ).first()
            
            if existing:
                existing.value = value
            else:
                new_value = ComparisonValue(
                    category_id=category_id,
                    brand_id=brand_id,
                    parameter_id=parameter_id,
                    value=value
                )
                session.add(new_value)
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"设置参数值失败: {e}")
            return False
        finally:
            session.close()
    
    def get_value(self, brand_id: int, parameter_id: int) -> Optional[str]:
        """获取参数值"""
        session = self.get_session()
        try:
            value_obj = session.query(ComparisonValue).filter(
                and_(
                    ComparisonValue.brand_id == brand_id,
                    ComparisonValue.parameter_id == parameter_id
                )
            ).first()
            
            return value_obj.value if value_obj else None
        finally:
            session.close()
    
    def get_table_data(self, category_id: int) -> Dict:
        """
        获取类目的完整表格数据
        
        Returns:
            {
                'brands': [{'id': 1, 'name': '希喂', 'is_own': 1}, ...],
                'parameters': [{'id': 1, 'name': '价格'}, ...],
                'values': {(brand_id, parameter_id): value, ...}
            }
        """
        session = self.get_session()
        try:
            # 获取品牌列表
            brands = session.query(ComparisonBrand).filter(
                ComparisonBrand.category_id == category_id
            ).order_by(ComparisonBrand.sort_order).all()
            
            # 获取参数列表
            parameters = session.query(ComparisonParameter).filter(
                ComparisonParameter.category_id == category_id
            ).order_by(ComparisonParameter.sort_order).all()
            
            # 获取所有值
            values_query = session.query(ComparisonValue).filter(
                ComparisonValue.category_id == category_id
            ).all()
            
            values_dict = {
                (v.brand_id, v.parameter_id): v.value 
                for v in values_query
            }
            
            return {
                'brands': [b.to_dict() for b in brands],
                'parameters': [p.to_dict() for p in parameters],
                'values': values_dict
            }
            
        finally:
            session.close()
    
    # ==================== 配置管理 ====================
    
    def save_config(self, config_type: str, config_dict: Dict) -> bool:
        """保存配置"""
        session = self.get_session()
        try:
            # 查找是否已存在
            config = session.query(ComparisonConfig).filter(
                ComparisonConfig.config_type == config_type
            ).first()
            
            if config:
                config.set_config_dict(config_dict)
            else:
                config = ComparisonConfig(config_type=config_type)
                config.set_config_dict(config_dict)
                session.add(config)
            
            session.commit()
            logger.info(f"保存配置成功: {config_type}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"保存配置失败: {e}")
            return False
        finally:
            session.close()
    
    def get_config(self, config_type: str) -> Optional[Dict]:
        """获取配置"""
        session = self.get_session()
        try:
            config = session.query(ComparisonConfig).filter(
                ComparisonConfig.config_type == config_type
            ).first()
            
            return config.get_config_dict() if config else None
        finally:
            session.close()
    
    # ==================== Excel 导入 ====================
    
    def import_from_excel_data(self, category_id: int, data: List[List[str]]) -> bool:
        """
        从Excel数据导入
        
        Args:
            category_id: 类目ID
            data: 二维数组，第一行为品牌名，第一列为参数名
                  [[空, 品牌1, 品牌2, ...],
                   [参数1, 值1, 值2, ...],
                   [参数2, 值1, 值2, ...]]
        """
        session = self.get_session()
        try:
            if not data or len(data) < 2:
                return False
            
            # 解析品牌（第一行，跳过第一个单元格）
            brand_names = data[0][1:]
            brand_objects = []
            
            for idx, brand_name in enumerate(brand_names):
                if brand_name.strip():
                    brand = self.add_brand(category_id, brand_name.strip(), sort_order=idx)
                    if brand:
                        brand_objects.append(brand)
            
            # 解析参数和值（从第二行开始）
            for row_idx, row in enumerate(data[1:]):
                if not row or len(row) < 2:
                    continue
                
                param_name = row[0].strip()
                if not param_name:
                    continue
                
                # 添加参数
                parameter = self.add_parameter(category_id, param_name, sort_order=row_idx)
                if not parameter:
                    continue
                
                # 添加每个品牌的参数值
                for col_idx, value in enumerate(row[1:]):
                    if col_idx < len(brand_objects):
                        brand = brand_objects[col_idx]
                        self.set_value(category_id, brand.id, parameter.id, value.strip())
            
            logger.info(f"Excel数据导入成功: 类目ID={category_id}")
            return True
            
        except Exception as e:
            logger.error(f"Excel数据导入失败: {e}")
            return False
    
    # ==================== 任务管理 ====================
    
    def add_task(
        self, 
        category_id: int, 
        task_name: str,
        insert_mode: str = 'column',
        insert_column: int = 1,
        insert_anchor_text: str = None,
        style_config: Dict = None,
        sort_order: int = 0
    ) -> Optional[ComparisonTask]:
        """
        添加新任务
        
        Args:
            category_id: 类目ID
            task_name: 任务名称
            insert_mode: 插入模式
            insert_column: 插入列号
            insert_anchor_text: 锚点文本
            style_config: 样式配置
            sort_order: 排序
            
        Returns:
            创建的任务对象或None
        """
        session = self.get_session()
        try:
            task = ComparisonTask(
                category_id=category_id,
                task_name=task_name,
                insert_mode=insert_mode,
                insert_column=insert_column,
                insert_anchor_text=insert_anchor_text,
                sort_order=sort_order
            )
            
            if style_config:
                task.set_style_dict(style_config)
            
            session.add(task)
            session.commit()
            session.refresh(task)
            
            logger.info(f"添加任务成功: {task_name}")
            return task
            
        except Exception as e:
            session.rollback()
            logger.error(f"添加任务失败: {e}")
            return None
        finally:
            session.close()
    
    def delete_task(self, task_id: int) -> bool:
        """删除任务"""
        session = self.get_session()
        try:
            task = session.query(ComparisonTask).filter(
                ComparisonTask.id == task_id
            ).first()
            
            if task:
                session.delete(task)
                session.commit()
                logger.info(f"删除任务成功: ID={task_id}")
                return True
            return False
            
        except Exception as e:
            session.rollback()
            logger.error(f"删除任务失败: {e}")
            return False
        finally:
            session.close()
    
    def update_task(self, task_id: int, **kwargs) -> bool:
        """更新任务信息"""
        session = self.get_session()
        try:
            task = session.query(ComparisonTask).filter(
                ComparisonTask.id == task_id
            ).first()
            
            if not task:
                return False
            
            for key, value in kwargs.items():
                if key == 'style_config' and isinstance(value, dict):
                    task.set_style_dict(value)
                elif hasattr(task, key):
                    setattr(task, key, value)
            
            session.commit()
            logger.info(f"更新任务成功: ID={task_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"更新任务失败: {e}")
            return False
        finally:
            session.close()
    
    def get_tasks_by_category(self, category_id: int) -> List[ComparisonTask]:
        """获取类目下的所有任务（按排序顺序）"""
        session = self.get_session()
        try:
            return session.query(ComparisonTask).filter(
                ComparisonTask.category_id == category_id
            ).order_by(ComparisonTask.sort_order).all()
        finally:
            session.close()
    
    def get_task_by_id(self, task_id: int) -> Optional[ComparisonTask]:
        """根据ID获取任务"""
        session = self.get_session()
        try:
            return session.query(ComparisonTask).filter(
                ComparisonTask.id == task_id
            ).first()
        finally:
            session.close()
    
    def reorder_tasks(self, task_ids: List[int]) -> bool:
        """重新排序任务"""
        session = self.get_session()
        try:
            for idx, task_id in enumerate(task_ids):
                task = session.query(ComparisonTask).filter(
                    ComparisonTask.id == task_id
                ).first()
                if task:
                    task.sort_order = idx
            
            session.commit()
            logger.info("任务排序更新成功")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"任务排序失败: {e}")
            return False
        finally:
            session.close()
    
    # ==================== 参数选择管理 ====================
    
    def set_task_parameters(self, task_id: int, parameter_ids: List[int]) -> bool:
        """
        设置任务的参数选择
        
        Args:
            task_id: 任务ID
            parameter_ids: 参数ID列表
            
        Returns:
            是否成功
        """
        session = self.get_session()
        try:
            # 先删除旧的选择
            session.query(TaskParameterSelection).filter(
                TaskParameterSelection.task_id == task_id
            ).delete()
            
            # 添加新的选择
            for param_id in parameter_ids:
                selection = TaskParameterSelection(
                    task_id=task_id,
                    parameter_id=param_id
                )
                session.add(selection)
            
            session.commit()
            logger.info(f"任务参数设置成功: task_id={task_id}, 参数数={len(parameter_ids)}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"设置任务参数失败: {e}")
            return False
        finally:
            session.close()
    
    def get_task_parameters(self, task_id: int) -> List[int]:
        """
        获取任务选择的参数ID列表
        
        Args:
            task_id: 任务ID
            
        Returns:
            参数ID列表
        """
        session = self.get_session()
        try:
            selections = session.query(TaskParameterSelection).filter(
                TaskParameterSelection.task_id == task_id
            ).all()
            
            return [s.parameter_id for s in selections]
        finally:
            session.close()
    
    def clear_task_parameters(self, task_id: int) -> bool:
        """清空任务的参数选择"""
        session = self.get_session()
        try:
            session.query(TaskParameterSelection).filter(
                TaskParameterSelection.task_id == task_id
            ).delete()
            
            session.commit()
            logger.info(f"清空任务参数成功: task_id={task_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"清空任务参数失败: {e}")
            return False
        finally:
            session.close()
    
    def get_task_full_data(self, task_id: int) -> Optional[Dict]:
        """
        获取任务的完整数据（包括参数列表）
        
        Returns:
            {
                'task': task对象,
                'selected_parameter_ids': [1, 2, 3],
                'parameters': [参数对象列表]
            }
        """
        session = self.get_session()
        try:
            task = session.query(ComparisonTask).filter(
                ComparisonTask.id == task_id
            ).first()
            
            if not task:
                return None
            
            # 获取选中的参数ID
            selected_ids = self.get_task_parameters(task_id)
            
            # 获取参数对象
            if selected_ids:
                parameters = session.query(ComparisonParameter).filter(
                    ComparisonParameter.id.in_(selected_ids)
                ).all()
            else:
                parameters = []
            
            return {
                'task': task,
                'selected_parameter_ids': selected_ids,
                'parameters': parameters
            }
            
        finally:
            session.close()

