# -*- coding: utf-8 -*-
"""
公共解析函数模块
提供MML命令解析的通用功能
"""
import re
from typing import Dict, List, Optional


def parse_key_value_pairs(text: str) -> Dict[str, str]:
    """
    解析键值对，如 ID=201,NAME="ToJSZUSPP01_SCTP_SYN_01",LOCPORT=5001
    
    Args:
        text: 键值对字符串
        
    Returns:
        键值对字典
    """
    result = {}
    # 使用正则匹配 KEY=VALUE 或 KEY="value" 格式
    pattern = r'(\w+)=(?:"([^"]*)"|([^,]*))'
    matches = re.findall(pattern, text)

    for key, quoted_val, unquoted_val in matches:
        value = quoted_val if quoted_val else unquoted_val
        value = value.strip()
        result[key] = value

    return result


def parse_any_command(line: str) -> Optional[Dict[str, any]]:
    """
    解析任意SET或ADD命令
    
    Args:
        line: MML命令行
        
    Returns:
        解析后的命令字典，包含 table, values, cmd_type 字段；解析失败返回None
    """
    match = re.match(r'(SET|ADD)\s+(\w+):(.+)', line.strip())
    if match:
        cmd_type = match.group(1)
        table_name = match.group(2)
        values_str = match.group(3)
        
        # 去除末尾的分号
        if values_str.endswith(';'):
            values_str = values_str[:-1]
            
        values = parse_key_value_pairs(values_str)
        return {'table': table_name, 'values': values, 'cmd_type': cmd_type}
    return None


def parse_mml_file(file_path: str, encoding: str = 'utf-8') -> Dict[str, List[Dict]]:
    """
    解析MML文件，返回按表分组的数据
    
    Args:
        file_path: MML文件路径
        encoding: 文件编码
        
    Returns:
        按表名分组的命令字典 {table_name: [{'values': {...}, 'cmd_type': 'SET'}, ...]}
    """
    with open(file_path, 'r', encoding=encoding) as f:
        lines = f.readlines()
    
    configs_by_table = {}
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('--') or line.startswith('ENTER'):
            continue
            
        if line.startswith('SET') or line.startswith('ADD'):
            config = parse_any_command(line)
            if config:
                table_name = config['table']
                if table_name not in configs_by_table:
                    configs_by_table[table_name] = []
                configs_by_table[table_name].append(config)
    
    return configs_by_table
