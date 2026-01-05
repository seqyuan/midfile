"""配置文件管理模块"""
import os
import yaml
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_config_path():
    """获取配置文件路径"""
    # 优先使用 XDG_CONFIG_HOME，否则使用 ~/.config
    config_home = os.environ.get('XDG_CONFIG_HOME')
    if config_home:
        config_dir = Path(config_home)
    else:
        config_dir = Path.home() / '.config'
    
    # 确保目录存在
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / 'midfile.yml'


def get_package_config_path():
    """获取包中的配置文件路径"""
    try:
        # Python 3.9+ 使用 importlib.resources
        from importlib.resources import files
        return files('midfile') / 'midfile.yml'
    except ImportError:
        # Python 3.8 使用 importlib_resources
        try:
            from importlib_resources import files
            return files('midfile') / 'midfile.yml'
        except ImportError:
            # 回退方案：使用 __file__
            import midfile
            package_dir = Path(midfile.__file__).parent
            return package_dir / 'midfile.yml'


def _create_default_config(config_path):
    """创建默认配置文件"""
    default_config = {
        'dbpath': '/data/midfile.db',
        'cloud': {
            'access_key': '',
            'secret_key': '',
            'endpoint': '',
            'bucket': ''
        }
    }
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False)
    logger.info(f'已创建默认配置文件: {config_path}')


def init_user_config():
    """初始化用户配置文件，从包中拷贝"""
    user_config_path = get_config_path()
    package_config_path = get_package_config_path()
    
    # 如果用户配置文件不存在，从包中拷贝
    if not user_config_path.exists():
        # 尝试从包中读取配置文件
        try:
            # 如果 package_config_path 是 Traversable 对象（importlib.resources）
            if hasattr(package_config_path, 'read_bytes'):
                config_content = package_config_path.read_bytes()
                with open(user_config_path, 'wb') as f:
                    f.write(config_content)
                logger.info(f'已从包中拷贝配置文件到: {user_config_path}')
            elif package_config_path.exists():
                # 如果是普通路径对象
                shutil.copy(package_config_path, user_config_path)
                logger.info(f'已从包中拷贝配置文件到: {user_config_path}')
            else:
                # 包中没有配置文件，创建默认配置
                _create_default_config(user_config_path)
        except Exception as e:
            logger.warning(f'无法从包中拷贝配置文件: {e}，将创建默认配置')
            _create_default_config(user_config_path)


def load_config():
    """加载配置文件"""
    config_path = get_config_path()
    
    # 如果配置文件不存在，先初始化
    if not config_path.exists():
        init_user_config()
    
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
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    logger.info(f'已更新配置文件 dbpath: {dbpath}')


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

