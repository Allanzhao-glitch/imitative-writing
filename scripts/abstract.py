# -*- coding:utf-8 -*-
import hashlib
import math
import os
from dataclasses import dataclass
from pathlib import Path
from shutil import copy
from signal import SIGINT, SIGTERM, signal
from threading import Thread
from time import sleep

from lib import Constants
from lib.exceptions import ConfigInitExitError, RustBinNotFoundError
from lib.setting import Settings
from lib.time_converter import TimeConverter
from lib.trace import TraceLogger
from scripts.shell import SSHManager


@dataclass
class MetricSummary:
    """计算结果"""

    max: int | float | None
    """最大值"""
    min: int | float | None
    """最小值"""
    avg: int | float | None
    """平均值"""
    ratio: int | float | None
    """占比"""


class abstract(TraceLogger, SSHManager, TimeConverter):
    def __init__(self):
        self.ini_handler = Constants.INI_HANDLER
        targets = self.ini_handler.read_data.get("TARGETS", {})
        log_config = self.ini_handler.read_data.get("LOGGING", {})
        SSHManager.__init__(self)
        TraceLogger.__init__(
            self,
            level=log_config.get("level", "info"),
            log_file_name=log_config.get("level_name", "default.log"),
        )
        self.exit_countdown = 3
        self.cachedir = Constants.CACHE_DIR
        self.rustbindir = Constants.RUSTBIN_DIR
        self.runtimelog = Constants.RUNTIME_LOG
        self.test_targets = targets.get("path", "/userdata/")
        self.isrunning = True
        self.setup_signal_handler()
        self.settings = Settings

        self.shell_config = self.ini_handler.read_data.get("SHELL_CONFIG")
        if self.shell_config is None:
            self.shell_config = self.settings.SHELL_CONFIG
            self.log_warning(f"当前配置文件不存在ssh配置项,或不存在配置文件读取默认配置: {self.settings.SHELL_CONFIG}")
        self.shell_ip = self.shell_config["ip"]
        self.shell_port = self.shell_config["port"]
        self.shell_username = self.shell_config["username"]
        self.shell_password = self.shell_config["password"]

        self.running_time = None
        self.unit_chinese = None
        self.start_time = 0
        self.end_time = 0
        self.elapsed_time = 0

        self.fail_count = 0
        self.total_count = 0
        self.current_count = 0
        self.success_count = 0

        self._scpclient = None
        self._is_summary = False

    @property
    def scpclient(self):
        """内部调用返回SCPClient对象避免部分用例不需要该对象仍被导入

        Returns:
            SCPClient: SCPClient对象
        """
        if self._scpclient:
            return self._scpclient
        else:
            from scp import SCPClient

            self._scpclient = SCPClient
            return self._scpclient

    def config_init(self, *args, **kwargs):
        """ini配置文件初始化函数"""

        if not Path(Constants.CONFIG_INI_PATH).exists():
            self.ini_handler.create_file()
            write = self.ini_handler.write_data
            default_settings = {
                "TARGETS": self.settings.TARGETS,
                "LOGGING": self.settings.LOGGING,
                "SHELL_CONFIG": self.settings.SHELL_CONFIG,
            }
            for key, value in {**default_settings, **kwargs}.items():
                write(key, value)
            self.log_warning(
                f"首次启动脚本,创建配置文件并且写入默认SSH配置: {self.settings.SHELL_CONFIG} ,默认日志配置: {self.settings.LOGGING} ,默认测试目录: {self.settings.TARGETS}"
            )
            comment_list = [
                "TARGETS.path:被测试端的操作目录",
                "LOGGING.level:日志打印等级, 默认为info",
                "SHELL_CONFIG.ip:被测试端IP,必填",
                "SHELL_CONFIG.port:被测试端远程端口,必填",
                "SHELL_CONFIG.username:被测试端登录用户,必填",
                "SHELL_CONFIG.password:被测试端登录密码,必填",
            ] + list(args)
            self.ini_handler.write_comment(*comment_list)
            raise ConfigInitExitError("SSH运行配置初始化本次运行退出")

    def log_summary(self):
        """结果日志打印方法"""
        if self._is_summary:
            return
        self._is_summary = True
        self.elapsed_time = self.end_time - self.start_time
        self.log_info(
            f"预期运行时间:[{self.unit_chinese}], 实际运行时间:[{self.seconds_to_time(self.elapsed_time)}]",
            stack=3,
        )
        self.log_info(
            f"总运行次数:[{self.total_count}], 测试成功次数:[{self.success_count}], 测试失败次数:[{self.fail_count}]",
            stack=3,
        )

    def reset_summary(self):
        """重置结果日志打印状态"""
        self.running_time = None
        self.unit_chinese = None
        self.start_time = 0
        self.end_time = 0
        self.elapsed_time = 0

        self.fail_count = 0
        self.total_count = 0
        self.current_count = 0
        self.success_count = 0
        self._is_summary = False

    @staticmethod
    def calculate_md5(file_path: str | Path, chunk_size: int = 8192) -> str:
        """计算文件md5值

        Args:
            file_path (str | Path): 文件路径
            chunk_size (int, optional): 每次读取文件的大小. Defaults to 8192.

        Raises:
            FileNotFoundError: 文件路径未找到时错误

        Returns:
            str: 计算出的MD5值
        """
        md5 = hashlib.md5()
        if not Path(file_path).exists():
            raise FileNotFoundError("需要计算MD5值的文件未找到")
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                md5.update(chunk)
        return md5.hexdigest()

    def generate_random_file(self, file_name: str, size_in_mb: int = 10) -> Path:
        """生成一个随机文件写入缓存目录,以生成的文件不会重复生成仅返回文件路径

        Args:
            file_name (str): 随机文件名
            size_in_mb (int, optional): 随机文件大小,单位MB. Defaults to 10MB.

        Returns:
            Path: 创建的文件路径
        """
        write_path = self.cachedir / str(file_name)
        if not write_path.exists():
            file_size = size_in_mb * 1024 * 1024
            with open(write_path, "wb") as f:
                f.write(os.urandom(file_size))
        return write_path

    def setup_signal_handler(self):
        """捕捉关闭信号,通过修改aborted的值告知程序已关闭.所有执行程序内都需要添加aborted在循环节点以进行控制"""

        def signal_handler(signum, frame):
            self.log_critical("主动关闭信号已捕捉开始关闭程序")
            self.log_critical("用户手动中断测试,执行中的测试数据未进行回收")
            self.isrunning = False
            shutdown = Thread(target=self.terminate_processing)
            shutdown.start()

        signal(SIGINT, signal_handler)
        signal(SIGTERM, signal_handler)

    def terminate_processing(self):
        """子线程倒计时强制关闭程序"""
        self.wait_with_delay("程序强制关闭倒计时", self.exit_countdown, "warning")
        self.log_summary()
        os._exit(0)

    def load_config(self, sections: str) -> dict | None:
        """读取ini文件某一个sections是否存在

        Args:
            sections (str): sections key

        Returns:
            dict | None: 存在返回可读取对象，不存在时返回None
        """
        return self.ini_handler.read_data.get(sections, None)

    @staticmethod
    def calculate_statistics(data_list: list, value=None) -> MetricSummary:
        """计算一个list中的最大、最小、平均数值，和某一个数值在list中的占比

        Args:
            data_list (list): 需要计算的list
            value (T): 任意类型需要计算占比的数据

        Returns:
            tuple[int, float, None]: 返回格式,最大值、最小值、平均值、计算占比的比例
        """
        if not data_list:
            return MetricSummary(None, None, None, None)

        # 只保留有效的数值（排除 NaN/Inf 和非数值）
        numeric_data = [
            x
            for x in data_list
            if isinstance(x, (int, float)) and not (isinstance(x, float) and (math.isinf(x) or math.isnan(x)))
        ]

        if numeric_data:
            max_value = max(numeric_data)
            min_value = min(numeric_data)
            average_value = sum(numeric_data) / len(numeric_data)
            avg_formatted = f"{average_value:.2f}"
        else:
            max_value = None
            min_value = None
            avg_formatted = None

        count_value = data_list.count(value)

        # 明确判断是否需要计算占比（允许 value 为 0 或 空字符串）
        if value is not None:
            _percentage = (count_value / len(data_list)) * 100 if len(data_list) > 0 else 0
            percentage = f"{_percentage:.2f}"
        else:
            percentage = None

        return MetricSummary(max_value, min_value, avg_formatted, percentage)

    def copy_to_runtimelog(self, source: str | Path, name: str):
        """复制文件到runtimelog目录

        Args:
            source (str | Path): 源文件地址
            destination (str | Path): 复制文件名称目录固定为runtime_log目录
        """
        destination = self.runtimelog / name
        copy(source, destination)

    def scp_to_runtimelog(self, source: str | Path):
        """使用scp下载指定文件到runtimelog目录

        Args:
            source (str | Path): 远端文件路径
        """
        with self.scpclient(self.get_transport()) as scp_clinet:
            scp_clinet.get(source, self.runtimelog)

    def find_rustbin(self, rustbin: str | Path) -> Path:
        """查找所需的rustbin执行文件

        Args:
            rustbin (str | Path): 文件名称或者是扩展路径

        Raises:
            RustBinNotFoundError: 未找到抛出异常

        Returns:
            Path: 存在的执行文件路径
        """
        rustbindir = Constants.PROJECT_BASE_DIR / rustbin
        rustbinbase = self.rustbindir / rustbin
        if rustbindir.exists():
            return rustbindir
        elif rustbinbase.exists():
            return rustbinbase
        else:
            raise RustBinNotFoundError(f"未找到所需执行文件,已查找: {rustbindir} 和 {rustbinbase}")

    def wait_with_delay(self, description: str | None = None, countdown: int = 0, log_key: str = "debug"):
        """倒计时方法

        Args:
            description (str | None, optional): 描述倒计时调用对象的介绍. Defaults to None.
            countdown (int, optional): 倒计时时间. 默认不设置时间直接跳过 0.
            log_key (str, optional): 设置打印log的等级. Defaults to "debug".
        """
        log_map = {
            "debug": self.log_debug,
            "info": self.log_info,
            "warning": self.log_warning,
            "error": self.log_error,
            "critical": self.log_critical,
        }
        log_value = log_map.get(log_key.lower(), self.log_debug)
        if countdown:
            if description:
                log_value(f"{description},倒计时{countdown}秒", stack=3)
            for remaining in range(countdown, 0, -1):
                log_value(f"倒计时: {remaining} 秒", stack=3)
                sleep(1)
        else:
            log_value("未设置倒计时时间直接跳过", stack=2)

    def is_executable_exists(self, remote_path: str | Path, local_path: str | Path):
        """验证执行文件车机端是否存在

        Args:
            remote_path (str | Path): 车机端执行名路劲默认为测速路径
            local_path (str | Path): 本地文件路径
        """
        self.log_debug(f"验证测试执行文件 {remote_path} 是否存在")
        message = self.execute(f"test -e {self.test_targets}{remote_path} && echo 'true' || echo 'false'")
        if message.stdout == "false":
            self.log_info("测试执行文件未找到开始上传", stack=3)
            with self.scpclient(self.get_transport()) as scp_clinet:
                scp_clinet.put(local_path, self.test_targets)
                self.log_info("测试执行文件上传完成", stack=3)

        message = self.execute(f"test -x {self.test_targets}{remote_path} && echo 'true' || echo 'false'")
        self.log_debug("查看测试执行文件是否有执行权限", stack=3)
        if message.stdout == "false":
            self.log_info("测试执行文件没有执行权限", stack=3)
            self.execute(f"chmod +x {self.test_targets}{remote_path}")
            self.log_info("赋予执行权限成功", stack=3)

    def is_directory_present(self, directory: str) -> None:
        """传入Linux文件夹路径验证文件夹是否存在如何不存在创建该文件夹

        Args:
            directory (str): 文件夹路径
        """
        self.execute(f"[ -d '{directory}' ] || mkdir -p '{directory}'")

    def get_pid_by_cmd(self, cmd: str) -> None | str:
        """根据命令获取进程ID

        Args:
            cmd (str): 要查找的命令字符串

        Returns:
            None | str: 找到的进程ID，未找到返回None
        """
        x3_cmd = f"ps w | grep '{cmd}' | grep -v 'grep' | awk '{{print $1}}'"
        x5_cmd = f"ps aux | grep '{cmd}' | grep -v 'grep' | awk '{{print $2}}'"
        if x3_stdout := self.execute(x3_cmd).stdout:
            return x3_stdout
        elif x5_stdout := self.execute(x5_cmd).stdout:
            return x5_stdout
        else:
            return None

    def get_tail_by_file(self, file_path: str, num: int | str = 1) -> None | str:
        """获取ssh远端指定文件最后一行

        Args:
            file_path (str): 指定文件
            num (int | str, optional): 指定获取行数. Defaults to 1.

        Returns:
            None | str: 获取到的结果，未找到返回None
        """
        message = self.execute(f"tail -n{num} {file_path}")
        return message.stdout if message.stdout else None

    def kill_process(self, pid: str, force: bool = False) -> None:
        """根据进程ID杀死进程

        Args:
            pid (str): 进程ID
            force (bool, optional): 是否强制杀死. Defaults to False.
        """
        signal = "-9" if force else ""
        self.execute(f"kill {signal} {pid}")
