# -*- coding:utf-8 -*-
class Settings:
    SHELL_CONFIG = {
        "ip": "192.168.1.75",
        "port": "33089",
        "username": "root",
        "password": "Ag8l3x",
    }
    LOGGING = {"level": "info"}
    TARGETS = {"path": "/userdata/"}

    USB_SERIAL = {
        "port": "/dev/ttyUSB0",
        "baudrate": "9600",
        "timeout": "3",
        "module_number": "1",
        "line_number": "1",
    }

    RUN_SLEEP = {"touch_time": "1.5", "on_time": "3", "off_time": "3"}
