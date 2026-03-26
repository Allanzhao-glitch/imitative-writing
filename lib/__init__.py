from pathlib import Path

from .basics_path import path_anchor
from .tools_config import IniFileHandler

def ensure_directory_exists(directory: Path):
    """验证目录是否存在,不存在时创建

    Args:
        directory (Path): 目录的path对象
    """
    if not directory.exists():
        directory.mkdir()

class Constants:
    PROJECT_BASE_DIR = path_anchor()
    assert isinstance(PROJECT_BASE_DIR, Path), f"项目初始化获取路径错误: {PROJECT_BASE_DIR}"
    CONFIG_INI_PATH = PROJECT_BASE_DIR / "config.ini"
    CACHE_DIR = PROJECT_BASE_DIR / "cache"
    RUNTIME_LOG = PROJECT_BASE_DIR / "runtime_log"
    RUSTBIN_DIR = PROJECT_BASE_DIR / "rustbin"
    INI_HANDLER = IniFileHandler(CONFIG_INI_PATH)


ensure_directory_exists(Constants.CACHE_DIR)
ensure_directory_exists(Constants.RUNTIME_LOG)