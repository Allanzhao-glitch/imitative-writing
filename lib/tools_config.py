# -*- coding:utf-8 -*-

from configparser import ConfigParser


class IniFileHandler(ConfigParser):
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def create_file(self):
        """创建一个新的INI文件"""
        with open(self.file_path, "w", encoding="utf-8"):
            pass

    def write_data(self, section: str, data_dict: dict):
        """向INI文件中写入数据

        Args:
            section (str): 配置节名称
            data_dict (dict): 需要写入的字典
        """
        if not self.has_section(section):
            self.add_section(section)
        for key, value in data_dict.items():
            self.set(section, key, value)
        with open(self.file_path, "w", encoding="utf-8") as configfile:
            self.write(configfile)

    @property
    def read_data(self) -> dict:
        """从INI文件中读取所有数据"""
        self.read(self.file_path, encoding="utf-8")
        return dict(self.items())

    def write_comment(self, *comments: tuple):
        """向INI文件中写入注释"""
        with open(self.file_path, "a", encoding="utf-8") as configfile:
            for comment in comments:
                configfile.write(f"; {comment}\n")

    @property
    def read_all(self) -> dict:
        """用于调式为主一次性读取整个ini文件为一个字典"""
        self.read(self.file_path, encoding="utf-8")
        return {section: {key: self[section][key] for key in self[section]} for section in self.sections()}
