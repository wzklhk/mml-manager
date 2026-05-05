#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV/Excel转MML配置文件脚本
支持从目录读取CSV文件或单个Excel文件，转换回MML命令格式
"""
import os
import argparse
import pandas as pd
from typing import List, Dict
import glob

from utils.mml import format_mml_value_simple


def row_to_mml(table_name: str, row: Dict[str, any], cmd_type: str = "SET") -> str:
    """
    将一行数据转换为MML命令
    """
    params = []
    for key, value in row.items():
        if pd.isna(value) or str(value).strip() == "":
            continue
        
        formatted_val = format_mml_value_simple(value)
        if formatted_val:
            params.append(f"{key}={formatted_val}")
    
    if not params:
        return ""
        
    param_str = ",".join(params)
    return f"{cmd_type} {table_name}:{param_str};"


def process_csv_file(csv_path: str, cmd_type_default: str = "SET") -> List[str]:
    """
    处理单个CSV文件，返回MML命令列表
    """
    mml_lines = []
    table_name = os.path.splitext(os.path.basename(csv_path))[0]
    
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
    except Exception as e:
        print(f"[WARN] 无法读取文件 {csv_path}: {e}")
        return []
        
    if df.empty:
        return []
        
    # 确定命令类型：如果表名以ADD开头或特定逻辑，这里简化处理
    # 通常配置管理多为SET。如果用户希望区分，可以通过文件名前缀或参数控制
    # 这里默认使用传入的 cmd_type_default
    
    for _, row in df.iterrows():
        # 过滤掉全空的行
        if row.isnull().all():
            continue
            
        line = row_to_mml(table_name, row.to_dict(), cmd_type_default)
        if line:
            mml_lines.append(line)
            
    return mml_lines


def process_excel_file(excel_path: str, cmd_type_default: str = "SET") -> List[str]:
    """
    处理Excel文件，遍历所有Sheet，返回MML命令列表
    """
    mml_lines = []
    try:
        # 读取所有sheet
        xls = pd.ExcelFile(excel_path)
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            if df.empty:
                continue
                
            for _, row in df.iterrows():
                if row.isnull().all():
                    continue
                line = row_to_mml(sheet_name, row.to_dict(), cmd_type_default)
                if line:
                    mml_lines.append(line)
                    
    except Exception as e:
        print(f"[ERROR] 处理Excel文件 {excel_path} 失败: {e}")
        
    return mml_lines


def convert_to_mml(input_path: str, output_file: str, cmd_type: str = "SET"):
    """
    主转换逻辑
    """
    all_mml_lines = []
    
    if os.path.isfile(input_path):
        if input_path.endswith('.csv'):
            print(f"正在处理CSV文件: {input_path}")
            all_mml_lines.extend(process_csv_file(input_path, cmd_type))
        elif input_path.endswith(('.xlsx', '.xls')):
            print(f"正在处理Excel文件: {input_path}")
            all_mml_lines.extend(process_excel_file(input_path, cmd_type))
        else:
            print(f"[WARN] 不支持的文件格式: {input_path}")
            return
    elif os.path.isdir(input_path):
        print(f"正在扫描目录: {input_path}")
        csv_files = glob.glob(os.path.join(input_path, "*.csv"))
        if not csv_files:
            print("[WARN] 目录下未找到CSV文件")
            return
            
        for csv_file in sorted(csv_files):
            all_mml_lines.extend(process_csv_file(csv_file, cmd_type))
    else:
        print(f"[ERROR] 输入路径不存在: {input_path}")
        return
        
    # 写入输出文件
    if all_mml_lines:
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in all_mml_lines:
                f.write(line + "\n")
        print(f"[OK] MML文件已生成: {output_file}")
        print(f"     共生成 {len(all_mml_lines)} 条命令")
    else:
        print("[WARN] 未生成任何MML命令，请检查输入数据")


def main():
    parser = argparse.ArgumentParser(
        description='CSV/Excel转MML配置文件脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从目录中的CSV生成MML
  python csv2mml.py ./output/csv_dir -o result.mml

  # 从单个Excel文件生成MML
  python csv2mml.py config.xlsx -o result.mml

  # 指定命令类型为ADD (默认为SET)
  python csv2mml.py ./output/csv_dir -o result.mml --cmd-type ADD
        """
    )
    
    parser.add_argument('input_path', help='输入路径：CSV文件、Excel文件或包含CSV的目录')
    parser.add_argument('-o', '--output-file', default='result.mml', help='输出MML文件路径（默认：result.mml）')
    parser.add_argument('--cmd-type', default='SET', choices=['SET', 'ADD'], help='生成的MML命令类型（默认：SET）')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("CSV/Excel转MML脚本")
    print("=" * 60)
    print(f"输入: {args.input_path}")
    print(f"输出: {args.output_file}")
    print(f"命令类型: {args.cmd_type}")
    print()
    
    convert_to_mml(args.input_path, args.output_file, args.cmd_type)
    
    print("\n" + "=" * 60)
    print("转换完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()