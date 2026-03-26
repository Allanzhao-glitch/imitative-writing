__all__ = ["TraceLogger"]

from logging import Formatter, StreamHandler, getLogger
from logging.handlers import TimedRotatingFileHandler

from .basics_path import path_anchor

class ConstLog:
    formatters = {
        "debug": Formatter("%(levelname)s %(module)s %(lineno)d %(asctime)s : %(message)s"),
        "info": Formatter("%(levelname)s %(asctime)s : %(message)s"),
        "warning": Formatter("%(levelname)s %(asctime)s : %(message)s"),
        "error": Formatter("%(levelname)s %(asctime)s : %(message)s"),
        "critical": Formatter("%(levelname)s %(asctime)s : %(message)s"),
    }
    '''
        占位符	含义	示例
        %(levelname)s	日志级别名称	DEBUG, INFO, WARNING, ERROR, CRITICAL
        %(asctime)s	时间戳	2026-03-26 14:30:00
        %(message)s	日志消息内容	用户自定义的消息
        %(module)s	模块名	abstract, shell, latency_test
        %(lineno)d	行号	123
    '''
    def __init__(self,fmt_type:str,log_file_name:str):
        self.formatter = self.formatters.get(fmt_type.lower(),self.formatters["info"])
        self.screen = StreamHandler()
        self.screen.setFormatter(self.formatter)
        self.file_handler = TimedRotatingFileHandler(path_anchor().joinpath(log_file_name), "D", backupCount=10, encoding="utf-8")
        self.file_handler.setFormatter(self.formatter)

    def _layout(self):
        """
        设置日志格式
        asctime	        %(asctime)s	            日志事件发生的时间--人类可读时间，如：2003-07-08 16:49:45,896
        created	        %(created)f	            日志事件发生的时间--时间戳，就是当时调用time.time()函数返回的值
        relativeCreated	%(relativeCreated)d	    日志事件发生的时间相对于logging模块加载时间的相对毫秒数（目前还不知道干嘛用的）
        msecs	        %(msecs)d	            日志事件发生事件的毫秒部分
        levelname	    %(levelname)s	        该日志记录的文字形式的日志级别（'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'）
        levelno	        %(levelno)s	            该日志记录的数字形式的日志级别（10, 20, 30, 40, 50）
        name	        %(name)s	            所使用的日志器名称，默认是'root'，因为默认使用的是 rootLogger
        message	        %(message)s	            日志记录的文本内容，通过 msg % args计算得到的
        pathname	    %(pathname)s	        调用日志记录函数的源码文件的全路径
        filename	    %(filename)s	        pathname的文件名部分，包含文件后缀
        module	        %(module)s	            filename的名称部分，不包含后缀
        lineno	        %(lineno)d	            调用日志记录函数的源代码所在的行号
        funcName	    %(funcName)s	        调用日志记录函数的函数名
        process	        %(process)d	            进程ID
        processName	    %(processName)s	        进程名称，Python 3.1新增
        thread	        %(thread)d	            线程ID
        threadName	    %(thread)s	            线程名称

        """
        return self.formatter
    

class TraceLogger(ConstLog):
    LEVEL_VALUE = {"CRITICAL": 50, "ERROR": 40, "WARNING": 30, "INFO": 20, "DEBUG": 10}

    def __init__(self, level: str, log_file_name: str):
        super().__init__(fmt_type=level, log_file_name=log_file_name)
        if log_level := self.LEVEL_VALUE.get(level.upper()):
            self.console_logger = getLogger("log_console")
            self.file_logger = getLogger("log_file")
            self.console_logger.setLevel(log_level)
            self.console_logger.addHandler(self.screen)
            self.file_logger.setLevel(log_level)
            self.file_logger.addHandler(self.file_handler)
        else:
            raise ValueError(f"日志等级设置错误当前设置为: {level} \
                             支持设置类型: {list(self.LEVEL_VALUE.keys())} 不区分大小写")
        
    def log_debug(self, msg, stack=2):
        """打印debug等级日志

        Args:
            msg (any): 需要打印的内容
            stack (int, optional): 日志追踪深度. Defaults to 2.
        """
        self.console_logger.log(level=10, msg=msg, stacklevel=stack)
        self.file_logger.log(level=10, msg=msg, stacklevel=stack)

    def log_info(self, msg, stack=2):
        """打印info等级日志

        Args:
            msg (any): 需要打印的内容
            stack (int, optional): 日志追踪深度. Defaults to 2.
        """
        self.console_logger.log(level=20, msg=msg, stacklevel=stack)
        self.file_logger.log(level=20, msg=msg, stacklevel=stack)

    def log_warning(self, msg, stack=2):
        """打印warning等级日志

        Args:
            msg (any): 需要打印的内容
            stack (int, optional): 日志追踪深度. Defaults to 2.
        """
        self.console_logger.log(level=30, msg=msg, stacklevel=stack)
        self.file_logger.log(level=30, msg=msg, stacklevel=stack)

    def log_error(self, msg, stack=2):
        """打印error等级日志

        Args:
            msg (any): 需要打印的内容
            stack (int, optional): 日志追踪深度. Defaults to 2.
        """
        self.console_logger.log(level=40, msg=msg, stacklevel=stack)
        self.file_logger.log(level=40, msg=msg, stacklevel=stack)

    def log_critical(self, msg, stack=2):
        """打印critical等级日志

        Args:
            msg (any): 需要打印的内容
            stack (int, optional): 日志追踪深度. Defaults to 2.
        """
        self.console_logger.log(level=50, msg=msg, stacklevel=stack)
        self.file_logger.log(level=50, msg=msg, stacklevel=stack)
