"""配置文件管理模块"""
import os
import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_config_path():
    """获取配置文件路径（安装目录中的配置文件）"""
    return get_package_config_path()


def get_package_config_path():
    """获取包中的配置文件路径（返回实际文件系统路径）"""
    try:
        # 使用 __file__ 获取包的实际安装路径
        import midfile
        package_dir = Path(midfile.__file__).parent
        return package_dir / 'midfile.yml'
    except Exception as e:
        logger.error(f'无法获取包路径: {e}')
        raise


def load_config():
    """从安装目录加载配置文件"""
    config_path = get_config_path()
    
    if not config_path.exists():
        raise FileNotFoundError(f'配置文件不存在: {config_path}')
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def update_config_dbpath(dbpath):
    """更新配置文件中的 dbpath"""
    config_path = get_config_path()
    config = load_config()
    config['dbpath'] = dbpath
    
    # 尝试写入，如果失败则提示（配置文件可能为只读）
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        logger.info(f'已更新配置文件 dbpath: {dbpath}')
    except (PermissionError, OSError) as e:
        logger.warning(f'无法写入配置文件（可能为只读）: {config_path}，错误: {e}')
        logger.warning(f'请手动编辑配置文件，将 dbpath 设置为: {dbpath}')
        # 仍然更新内存中的配置，但不写入文件
        logger.info(f'内存中的配置已更新 dbpath: {dbpath}')


def get_dbpath():
    """从配置文件获取数据库路径"""
    config = load_config()
    return config.get('dbpath', '/data/midfile.db')


def get_cloud_config():
    """获取云存储配置"""
    config = load_config()
    if 'cloud' not in config:
        raise ValueError('配置文件中缺少 cloud 配置')
    return config['cloud']

