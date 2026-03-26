import sys
from pathlib import Path
from typing import Optional


def path_anchor() -> Optional[Path]:
    """获取工程目录锚点, 打包文件获取当前exe的文件路径
    Returns:
        Optional[Path]: 根目录的绝对路径
    """
    sys_argv = Path(sys.argv[0])
    if sys_argv.suffix == ".py":
        return Path(__file__).resolve().parents[1]
    else:
        return sys_argv.resolve().parent
