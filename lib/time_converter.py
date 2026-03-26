from dataclasses import dataclass
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass
class ParseTime:
    """格式化时间"""

    running_time: float
    """计算出来的总的运行时间，多少秒"""
    unit_chinese: str
    """运行时间的中文描述"""


class TimeConverter:
    units = {"W": 7 * 24 * 3600, "D": 24 * 3600, "H": 3600, "M": 60, "S": 1}
    units_chinese = {
        "W": "周",
        "D": "天",
        "H": "小时",
        "M": "分钟",
        "S": "秒",
    }

    try:
        CN_TZ = ZoneInfo("Asia/Shanghai")
    except ZoneInfoNotFoundError:
        from datetime import timedelta, timezone

        CN_TZ = timezone(timedelta(hours=8))

    @staticmethod
    def seconds_to_time(seconds: int | float) -> str:
        """将秒数转换为周、天、小时、分钟、秒

        Args:
            seconds(int | float): 要转换的秒数

        Returns:
            输出一共运行的时间
        """
        weeks = 604800
        days = 86400
        hours = 3600
        minutes = 60
        weeks_count = seconds // weeks
        seconds %= weeks
        days_count = seconds // days
        seconds %= days
        hours_count = seconds // hours
        seconds %= hours
        minutes_count = seconds // minutes
        seconds %= minutes
        result = ""
        if weeks_count > 0:
            result += f"{weeks_count}周"
        if days_count > 0:
            result += f"{days_count}天"
        if hours_count > 0:
            result += f"{hours_count}小时"
        if minutes_count > 0:
            result += f"{minutes_count}分"
        if seconds > 0:
            result += f"{seconds:.2f}秒"

        return result
    
    def parse_time(self, duration: None | str = None) -> tuple[float, str]:
        """把传入的字符时间变为时间戳支持格式:W周、D天、H小时、M分钟、S秒

        Args:
            duration (None | str, optional): 循环时间. 默认无限循环,支持单位：周、天、小时、分、秒.

        Returns:
            tuple: 已经计算完成的时间，中文时间单位
        """
        if duration:
            num, unit = int(duration[:-1]), duration[-1].upper()
            running_time = num * self.units.get(unit, 1)
            unit_chinese = str(num) + self.units_chinese.get(unit)
        else:
            running_time = float("inf")
            unit_chinese = "无限"
        return running_time, unit_chinese

