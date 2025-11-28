"""数据库管理模块"""

from .models import Material
from .db_manager import DatabaseManager

__all__ = ['Material', 'DatabaseManager']

