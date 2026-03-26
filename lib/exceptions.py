# -*- coding:utf-8 -*-
class RustBinNotFoundError(Exception):
    """Rust执行程序未找到错误"""

    def __init__(self, message):
        super().__init__(message)


class RelayControllerConnectionError(Exception):
    """串口连接继电器无法连接错误"""

    def __init__(self, message):
        super().__init__(message)


class RelayStateMismatchError(Exception):
    """继电器开关类型传入错误"""

    def __init__(self, message):
        super().__init__(message)


class RelayControllerValueError(Exception):
    """继电器模块号和端口号不存在值错误"""

    def __init__(self, message):
        super().__init__(message)


class SpeedTest4GDownloadUrlNotFoundError(Exception):
    """4G下载测速用例无法找到下载URL错误"""

    def __init__(self, message):
        super().__init__(message)


class ConfigInitExitError(Exception):
    """SSH运行配置初始化本次运行退出错误"""

    def __init__(self, message):
        super().__init__(message)


class TestConfigError(ValueError):
    """测试配置错误"""

    def __init__(self, message):
        super().__init__(message)
