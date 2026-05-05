#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MML配置管理Web服务 - Flask后端
提供MML文件导入、解析和基于SQLite的CRUD操作
"""
import os
import sys
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, g
from flask_cors import CORS

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.io_handler import read_mml_file
from utils.table import MmlDataSet

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 数据库配置
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mml_config.db')


def get_db():
    """获取数据库连接"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """关闭数据库连接"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """初始化数据库表结构"""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    
    # 创建配置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mml_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            cmd_type TEXT NOT NULL DEFAULT 'SET',
            config_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建索引
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_table_name ON mml_configs(table_name)
    ''')
    
    db.commit()
    db.close()
    print(f"[OK] 数据库初始化完成: {DATABASE}")


# ============================================================
# API路由
# ============================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


@app.route('/api/import-mml', methods=['POST'])
def import_mml():
    """导入MML文件并解析存储"""
    if 'file' not in request.files:
        return jsonify({'error': '未上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    
    if not file.filename.endswith('.mml'):
        return jsonify({'error': '只支持.mml格式文件'}), 400
    
    try:
        # 保存临时文件
        temp_path = os.path.join(os.path.dirname(DATABASE), f'temp_{datetime.now().timestamp()}.mml')
        file.save(temp_path)
        
        # 解析MML文件
        dataset = read_mml_file(temp_path, encoding='utf-8')
        
        if dataset.total_count == 0:
            os.remove(temp_path)
            return jsonify({'error': '未找到有效的MML命令'}), 400
        
        # 存储到数据库
        db = get_db()
        cursor = db.cursor()
        imported_count = 0
        
        for table_name in dataset.tables:
            group = dataset.get_group(table_name)
            if not group:
                continue
            
            for config in group.configs:
                import json
                config_json = json.dumps(config.values, ensure_ascii=False)
                cursor.execute(
                    'INSERT INTO mml_configs (table_name, cmd_type, config_data) VALUES (?, ?, ?)',
                    (table_name, config.cmd_type, config_json)
                )
                imported_count += 1
        
        db.commit()
        
        # 删除临时文件
        os.remove(temp_path)
        
        return jsonify({
            'message': f'成功导入 {imported_count} 条配置',
            'tables': dataset.tables,
            'total_count': imported_count
        })
    
    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'error': f'导入失败: {str(e)}'}), 500


@app.route('/api/configs', methods=['GET'])
def get_configs():
    """获取配置列表（支持分页和筛选）"""
    db = get_db()
    cursor = db.cursor()
    
    # 获取查询参数
    table_name = request.args.get('table_name')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    # 构建查询
    query = 'SELECT * FROM mml_configs WHERE 1=1'
    params = []
    
    if table_name:
        query += ' AND table_name = ?'
        params.append(table_name)
    
    # 获取总数
    count_query = query.replace('SELECT *', 'SELECT COUNT(*)')
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]
    
    # 分页查询
    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.extend([page_size, (page - 1) * page_size])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    configs = []
    for row in rows:
        import json
        config_data = json.loads(row['config_data'])
        configs.append({
            'id': row['id'],
            'table_name': row['table_name'],
            'cmd_type': row['cmd_type'],
            'config_data': config_data,
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        })
    
    return jsonify({
        'configs': configs,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size
    })


@app.route('/api/configs/<int:config_id>', methods=['GET'])
def get_config(config_id):
    """获取单个配置详情"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM mml_configs WHERE id = ?', (config_id,))
    row = cursor.fetchone()
    
    if not row:
        return jsonify({'error': '配置不存在'}), 404
    
    import json
    config_data = json.loads(row['config_data'])
    
    return jsonify({
        'id': row['id'],
        'table_name': row['table_name'],
        'cmd_type': row['cmd_type'],
        'config_data': config_data,
        'created_at': row['created_at'],
        'updated_at': row['updated_at']
    })


@app.route('/api/configs/<int:config_id>', methods=['PUT'])
def update_config(config_id):
    """更新配置"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据为空'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    # 检查配置是否存在
    cursor.execute('SELECT * FROM mml_configs WHERE id = ?', (config_id,))
    row = cursor.fetchone()
    
    if not row:
        return jsonify({'error': '配置不存在'}), 404
    
    # 更新配置
    import json
    config_data = json.dumps(data.get('config_data', {}), ensure_ascii=False)
    table_name = data.get('table_name', row['table_name'])
    cmd_type = data.get('cmd_type', row['cmd_type'])
    
    cursor.execute(
        'UPDATE mml_configs SET table_name = ?, cmd_type = ?, config_data = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        (table_name, cmd_type, config_data, config_id)
    )
    db.commit()
    
    return jsonify({'message': '配置更新成功'})


@app.route('/api/configs/<int:config_id>', methods=['DELETE'])
def delete_config(config_id):
    """删除配置"""
    db = get_db()
    cursor = db.cursor()
    
    # 检查配置是否存在
    cursor.execute('SELECT * FROM mml_configs WHERE id = ?', (config_id,))
    row = cursor.fetchone()
    
    if not row:
        return jsonify({'error': '配置不存在'}), 404
    
    # 删除配置
    cursor.execute('DELETE FROM mml_configs WHERE id = ?', (config_id,))
    db.commit()
    
    return jsonify({'message': '配置删除成功'})


@app.route('/api/tables', methods=['GET'])
def get_tables():
    """获取所有表名列表"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT DISTINCT table_name FROM mml_configs ORDER BY table_name')
    rows = cursor.fetchall()
    
    tables = [row['table_name'] for row in rows]
    
    return jsonify({'tables': tables})


@app.route('/api/export-mml', methods=['POST'])
def export_mml():
    """导出配置为MML文件"""
    data = request.get_json()
    table_name = data.get('table_name')
    
    db = get_db()
    cursor = db.cursor()
    
    # 查询配置
    if table_name:
        cursor.execute('SELECT * FROM mml_configs WHERE table_name = ? ORDER BY id', (table_name,))
    else:
        cursor.execute('SELECT * FROM mml_configs ORDER BY table_name, id')
    
    rows = cursor.fetchall()
    
    if not rows:
        return jsonify({'error': '没有可导出的配置'}), 404
    
    # 生成MML内容
    import json
    from utils.mml import format_mml_command
    
    mml_lines = []
    mml_lines.append(f"-- 由MML Manager导出\n")
    mml_lines.append(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    current_table = None
    for row in rows:
        if row['table_name'] != current_table:
            current_table = row['table_name']
            mml_lines.append(f"-- ===== {current_table} =====\n")
        
        config_data = json.loads(row['config_data'])
        line = format_mml_command(row['cmd_type'], row['table_name'], config_data)
        mml_lines.append(line + '\n')
    
    mml_content = ''.join(mml_lines)
    
    return jsonify({
        'content': mml_content,
        'filename': f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mml"
    })


if __name__ == '__main__':
    # 初始化数据库
    init_db()
    
    # 启动服务
    print("\n" + "=" * 60)
    print("MML配置管理Web服务启动中...")
    print("=" * 60)
    print(f"API地址: http://localhost:5000")
    print(f"数据库: {DATABASE}")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
