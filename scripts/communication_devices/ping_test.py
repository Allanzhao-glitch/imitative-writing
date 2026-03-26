__version__ = "1.0.0"

import argparse
import re
import sys
from time import sleep, time

from ping3 import ping

from scripts.abstract import abstract



class PingTest(abstract):
    def __init__(self):
        super().__init__()
        self.config_init(
            "LatencyTest.ping_host:测试目标IP地址",
            "LatencyTest.interval:测试延迟每一跳间隔时间，单位秒仅支持整数",
            "LatencyTest.interface:指定测试网卡，不设置或无此项默认使用默认网卡",
            "LatencyTest.duration:自动化脚本运行时间，不设置或无此项默认无限，支持单位：周w、天d、小时h、分m、秒s，不区分大小写示例: 10S 为运行十秒",
            PingTest={
                "ping_host": "",
                "interval": "1",
                "duration": "",
                "interface": "",
            },
        )
        runtime_config = self.load_config("PingTest") or {}
        self.duration = runtime_config.get("duration", None)
        self.interval = int(runtime_config.get("interval", 1))
        self.interface = runtime_config.get("interface", "")
        self._ping_host = runtime_config.get("ping_host", "")

    def ping_host(self) -> None:
        """测试ping延迟方法"""
        self.running_time, self.unit_chinese = self.parse_time(self.duration)
        self.start_time = time()
        ping_list = []
        if self.interface:
            self.log_info(f"指定网卡为{self.interface}")
            interface = self.interface
        else:
            self.log_info("未指定网卡，使用默认网卡")
            interface = ""

        if not self._ping_host:
            raise ValueError("未设置测试目标IP地址")
        
        while self.isrunning:
            result = self.execute(f"ping -c 4 {self._ping_host}")
            if result and result.returncode == 0:
                match = re.search(r'rtt min/avg/max/mdev = (\d+\.?\d*)/(\d+\.?\d*)/(\d+\.?\d*)/', result.stdout)
                if match:
                    avg_delay = float(match.group(2))
                    self.log_info(f"延迟测试，平均延迟: {avg_delay} ms, 目标: {self._ping_host}")
                    ping_list.append(avg_delay)
                    self.success_count += 1
                else:
                    self.log_warning(f"无法解析延迟结果: {result.stdout}")
                    ping_list.append("超时")
                    self.fail_count += 1
            else:
                self.log_warning(f"Ping {self._ping_host} 失败!!!")
                ping_list.append("超时")
                self.fail_count += 1
            self.total_count += 1
            sleep(self.interval)
            self.end_time = time()
            if self.end_time - self.start_time >= self.running_time:
                self.log_summary()
                break
        
        result = self.calculate_statistics(ping_list, "超时")
        self.log_info(f"最大延迟:{result.max}ms,最小延迟:{result.min}ms,平均延迟:{result.avg}ms,丢包率为:{result.ratio}%")
        self.log_summary()


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="车机自动化脚本 - 网络延迟测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            使用示例:
            python latency_test.py                # 运行延迟测试
            python latency_test.py --version      # 显示版本信息
            python latency_test.py --config       # 显示配置帮助

            注意: 首次运行前请确保已配置config.ini文件中的相关参数
        """,
    )

    parser.add_argument("--version", "-v", action="store_true", help="显示版本信息")

    parser.add_argument("--config", "-c", action="store_true", help="显示配置方法说明")

    return parser.parse_args()

def show_version():
    """显示版本信息"""
    print(f"延迟测试脚本 v{__version__}")
    print("车机自动化脚本工具包")
    print("功能：测试网络延迟并生成统计报告")


def show_config_help():
    """显示配置方法帮助信息"""
    print("配置方法说明:")
    print("=" * 50)
    print("1. 配置文件位置: config.ini")
    print()
    print("2. 配置项说明:")
    print("   [LatencyTest]")
    print("   ping_host    = 目标IP地址 (必填)")
    print("   interval     = 测试间隔时间，单位秒 (默认: 1)")
    print("   interface    = 指定网卡名称 (可选，默认使用系统默认网卡)")
    print("   duration     = 运行时间 (可选，支持单位: w/d/h/m/s，如: 10s)")
    print()
    print("   [SHELL_CONFIG]")
    print("   ip           = 被测试端IP地址")
    print("   port         = SSH端口号")
    print("   username     = SSH用户名")
    print("   password     = SSH密码")
    print()
    print("3. 配置示例:")
    print("   [LatencyTest]")
    print("   ping_host = 8.8.8.8")
    print("   interval = 1")
    print("   duration = 60s")
    print("   interface = eth0")
    print()
    print("4. 时间单位说明:")
    print("   - w: 周 (例: 1w = 1周)")
    print("   - d: 天 (例: 7d = 7天)")
    print("   - h: 小时 (例: 24h = 24小时)")
    print("   - m: 分钟 (例: 30m = 30分钟)")
    print("   - s: 秒 (例: 60s = 60秒)")
    print()
    print("5. 首次运行时，脚本会自动生成默认配置文件")


if __name__ == "__main__":
    args = parse_arguments()

    if args.version:
        show_version()
        sys.exit(0)

    if args.config:
        show_config_help()
        sys.exit(0)

    lt = PingTest()
    lt.ping_host()