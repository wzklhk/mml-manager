# -*- coding: utf-8 -*-
"""
控制层 (Controller)
Flask 路由定义，处理 HTTP 请求/响应。
"""
import os
from datetime import datetime
from flask import Blueprint, request, jsonify

from service import mml_service
from dao import mml_dao
from config import get_settings

# Blueprint 注册到 /api 前缀
api = Blueprint('api', __name__, url_prefix='/api')

# 数据库目录（用于存放临时文件）
DB_DIR = os.path.dirname(get_settings()['database']['path'])


@api.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


@api.route('/import-mml', methods=['POST'])
def import_mml():
    """导入 MML 文件"""
    if 'file' not in request.files:
        return jsonify({'error': '未上传文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    if not file.filename.endswith('.mml'):
        return jsonify({'error': '只支持.mml格式文件'}), 400

    temp_path = os.path.join(
        DB_DIR,
        f'temp_{datetime.now().timestamp()}.mml'
    )

    try:
        file.save(temp_path)
        result = mml_service.import_mml_file(temp_path)

        if 'error' in result:
            return jsonify(result), 400

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': f'导入失败: {str(e)}'}), 500

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@api.route('/tables', methods=['GET'])
def get_tables():
    """获取所有 MML 表"""
    try:
        tables = mml_service.get_tables_summary()
        return jsonify({'tables': tables})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/configs', methods=['GET'])
def get_configs():
    """
    获取配置列表。
    ?table_name=XXX&page=1&page_size=20   → 指定表分页
    无 table_name                          → 返回所有表概览
    """
    try:
        table_name = request.args.get('table_name', '').strip()
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        sort_by = request.args.get('sort_by') or None
        sort_order = request.args.get('sort_order', 'asc')

        if table_name:
            result = mml_service.get_configs(table_name, page, page_size, sort_by, sort_order)
        else:
            # 未指定表：返回概览
            summary = {}
            tables = mml_service.get_tables_summary()
            for t in tables:
                summary[t['table_name']] = {
                    'count': t['count'],
                    'columns': t['columns'],
                }
            result = {
                'tables_summary': summary,
                'configs': [],
                'total': 0,
                'page': 1,
                'page_size': page_size,
                'total_pages': 1,
            }

        return jsonify(result)

    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'查询失败: {str(e)}'}), 500


@api.route('/configs', methods=['POST'])
def add_config():
    """新增配置行"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求数据为空'}), 400

    table_name = data.get('table_name', '')
    config_data = data.get('config_data', {})
    if not table_name or not config_data:
        return jsonify({'error': '需要 table_name 和 config_data'}), 400

    try:
        new_id = mml_service.add_config(table_name, config_data)
        return jsonify({'message': '新增成功', 'id': new_id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'新增失败: {str(e)}'}), 500


@api.route('/configs/<int:config_id>', methods=['GET'])
def get_config(config_id):
    """获取单条配置"""
    table_name = request.args.get('table_name', '')
    if not table_name:
        return jsonify({'error': '需要指定 table_name 参数'}), 400

    try:
        config = mml_service.get_config(table_name, config_id)
        if not config:
            return jsonify({'error': '配置不存在'}), 404
        return jsonify(config)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/configs/<int:config_id>', methods=['PUT'])
def update_config(config_id):
    """更新配置行"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求数据为空'}), 400

    table_name = data.get('table_name', '')
    config_data = data.get('config_data', {})

    if not table_name:
        return jsonify({'error': '需要指定 table_name'}), 400

    try:
        success = mml_service.update_config(table_name, config_id, config_data)
        if not success:
            return jsonify({'error': '配置不存在'}), 404
        return jsonify({'message': '配置更新成功'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'更新失败: {str(e)}'}), 500


@api.route('/configs/<int:config_id>', methods=['DELETE'])
def delete_config(config_id):
    """删除配置行"""
    table_name = request.args.get('table_name', '')
    if not table_name:
        return jsonify({'error': '需要指定 table_name 参数'}), 400

    try:
        success = mml_service.delete_config(table_name, config_id)
        if not success:
            return jsonify({'error': '配置不存在'}), 404
        return jsonify({'message': '配置删除成功'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


@api.route('/configs/batch-delete', methods=['POST'])
def batch_delete_configs():
    """批量删除配置行"""
    data = request.get_json() or {}
    table_name = data.get('table_name', '')
    ids = data.get('ids', [])
    if not table_name or not ids:
        return jsonify({'error': '需要 table_name 和 ids'}), 400

    try:
        deleted = mml_service.batch_delete_configs(table_name, ids)
        return jsonify({'message': f'成功删除 {deleted} 条配置', 'deleted': deleted})
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'批量删除失败: {str(e)}'}), 500


@api.route('/export-mml', methods=['POST'])
def export_mml():
    """导出为 MML 文件"""
    data = request.get_json() or {}
    table_name = data.get('table_name')
    ids = data.get('ids')

    try:
        if ids:
            result = mml_service.export_selected_rows(table_name, ids)
        else:
            result = mml_service.export_mml(table_name)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'导出失败: {str(e)}'}), 500
