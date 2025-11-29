"""qsync 包的初始化文件

此模块导出 sync 函数，用于执行同步操作。
"""

# 从 sync 模块导入 sync 函数
from .sync import sync

# 定义公共接口
__all__ = ['sync']

# 版本信息（占位符，待后续填写）
__version__ = '1.0.0'
__author__ = 'Nexeora'