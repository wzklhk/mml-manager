# -*- coding: utf-8 -*-
"""
表名处理和数据模型模块。

提供表名规范化、MML命令数据模型等通用功能。
"""
import re
from typing import Dict, List, Optional, Any


# --- 表名处理 ---

def sanitize_table_name(name: str) -> str:
    """
    将任意字符串转为合法的MML表名。
    
    - 非字母数字下划线字符替换为下划线
    - 数字开头的表名加 T_ 前缀
    - 空字符串返回 'TABLE'

    Args:
        name: 原始名称（文件名、Sheet名等）

    Returns:
        合法的MML表名
    """
    if not name:
        return 'TABLE'
    table = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    if not table:
        return 'TABLE'
    if table[0].isdigit():
        table = f"T_{table}"
    return table


# --- MML配置数据模型 ---

class MmlConfig:
    """
    单条MML配置命令的数据模型。

    Attributes:
        cmd_type: 命令类型 (SET/ADD)
        table: 表名
        values: 键值对字典 {字段名: 字段值}
    """

    def __init__(self, cmd_type: str = 'SET', table: str = '', values: Optional[Dict[str, str]] = None):
        self.cmd_type = cmd_type.upper()
        self.table = table
        self.values = values or {}

    def to_dict(self) -> Dict[str, Any]:
        """转为基础字典格式（兼容旧代码）"""
        return {
            'cmd_type': self.cmd_type,
            'table': self.table,
            'values': dict(self.values),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'MmlConfig':
        """从基础字典创建"""
        return cls(
            cmd_type=d.get('cmd_type', 'SET'),
            table=d.get('table', ''),
            values=dict(d.get('values', {})),
        )

    def __repr__(self) -> str:
        return f"MmlConfig({self.cmd_type} {self.table}: {len(self.values)} fields)"


# --- 分组数据 ---

class TableGroup:
    """
    按表名分组的MML配置集合。

    Attributes:
        table_name: 表名
        configs: 配置列表
        columns: 所有出现的字段名集合
    """

    def __init__(self, table_name: str = ''):
        self.table_name = table_name
        self.configs: List[MmlConfig] = []
        self.columns: set = set()

    def add(self, config: MmlConfig):
        """添加一条配置，自动更新字段集合"""
        self.configs.append(config)
        self.columns.update(config.values.keys())

    def merge(self, other: 'TableGroup'):
        """合并另一个同表分组的数据"""
        for c in other.configs:
            self.add(c)

    @property
    def count(self) -> int:
        return len(self.configs)

    def __repr__(self) -> str:
        return f"TableGroup({self.table_name}: {self.count} configs, {len(self.columns)} columns)"


class MmlDataSet:
    """
    完整的MML配置数据集，包含多个表的分组数据。

    这是模块间的标准数据交换格式。
    """

    def __init__(self):
        self._groups: Dict[str, TableGroup] = {}

    def add(self, config: MmlConfig):
        """添加一条配置到对应分组"""
        table = config.table
        if table not in self._groups:
            self._groups[table] = TableGroup(table)
        self._groups[table].add(config)

    def add_from_dict(self, d: Dict[str, Any]):
        """从旧格式字典添加"""
        self.add(MmlConfig.from_dict(d))

    def get_group(self, table: str) -> Optional[TableGroup]:
        return self._groups.get(table)

    @property
    def tables(self) -> List[str]:
        """按字母顺序返回所有表名"""
        return sorted(self._groups.keys())

    @property
    def groups(self) -> Dict[str, TableGroup]:
        return self._groups

    @property
    def total_count(self) -> int:
        return sum(g.count for g in self._groups.values())

    def __repr__(self) -> str:
        return f"MmlDataSet({self.total_count} configs in {len(self._groups)} tables)"
