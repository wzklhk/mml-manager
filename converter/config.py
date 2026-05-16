# -*- coding: utf-8 -*-
"""
配置加载模块

从 config.yaml 加载配置，提供全局 settings 对象。
搜索顺序：
  1. 当前目录 ./config.yaml
  2. ~/.mml-manager/config.yaml
  3. 环境变量 MML_CONFIG_PATH

所有相对路径解析基于配置文件所在目录。
"""
import os
import yaml
from typing import Any, Dict

# ---- 默认配置 ----
DEFAULTS: Dict[str, Any] = {
    'server': {
        'host': '0.0.0.0',
        'port': 5000,
        'debug': True,
    },
    'database': {
        'path': 'mml_config.db',
    },
    'logging': {
        'level': 'INFO',
    },
}

_SETTINGS: Dict[str, Any] | None = None


def _find_config() -> str | None:
    """按优先级查找配置文件路径"""
    # 1. 环境变量指定
    env_path = os.environ.get('MML_CONFIG_PATH')
    if env_path and os.path.isfile(env_path):
        return env_path

    # 2. 当前目录（与 app.py 同级）
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
    if os.path.isfile(local_path):
        return local_path

    # 3. 用户家目录 ~/.mml-manager/config.yaml
    home_path = os.path.expanduser('~/.mml-manager/config.yaml')
    if os.path.isfile(home_path):
        return home_path

    return None


def _resolve_path(path: str, config_dir: str) -> str:
    """将相对路径解析为绝对路径（基于配置所在目录）"""
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(config_dir, path))


def _merge(base: Dict, override: Dict) -> Dict:
    """递归合并字典（override 覆盖 base）"""
    result = dict(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _merge(result[key], val)
        else:
            result[key] = val
    return result


def load_config() -> Dict[str, Any]:
    """
    加载配置：YAML 文件 + 环境变量覆盖 → 合并默认值。
    返回扁平化后的 dict，所有相对路径已解析为绝对路径。
    """
    global _SETTINGS

    settings = dict(DEFAULTS)  # 深拷贝

    config_path = _find_config()
    config_dir = os.path.dirname(config_path) if config_path else os.getcwd()

    if config_path:
        with open(config_path, 'r', encoding='utf-8') as f:
            # 支持无 yaml 依赖时的降级（但实际 yaml 是必需依赖）
            try:
                overrides = yaml.safe_load(f) or {}
                settings = _merge(settings, overrides)
            except ImportError:
                print("[WARN] PyYAML 未安装，使用默认配置。pip install pyyaml")
            except yaml.YAMLError as e:
                print(f"[WARN] 配置文件解析失败: {e}，使用默认配置")

    # 解析数据库路径
    db_path = settings['database']['path']
    settings['database']['path'] = _resolve_path(db_path, config_dir)

    # 确保数据库目录存在
    db_dir = os.path.dirname(settings['database']['path'])
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    _SETTINGS = settings
    return settings


def get_settings() -> Dict[str, Any]:
    """获取已加载的配置（懒加载）"""
    global _SETTINGS
    if _SETTINGS is None:
        load_config()
    return _SETTINGS
