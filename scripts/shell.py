__all__ = ["SSHManager"]   
'''
控制模块导入行为：当使用 from module import * 语句时，只有 __all__ 列表中指定的名称会被导入。这可以防止模块中的私有变量、函数或类被意外导入到其他模块中，从而避免命名冲突和代码污染。
明确模块公共接口：__all__ 列表清晰地表明了模块的设计者希望暴露给用户的公共 API。这有助于用户理解模块的用途和正确使用方法。
IDE 提示：一些集成开发环境（IDE）会根据 __all__ 列表提供代码补全和提示功能，方便开发者使用模块。
'''

from dataclasses import dataclass

from paramiko import SSHClient,AutoAddPolicy

@dataclass
class SSHCommandResult:
    stdout: str
    '''标准输出内容'''
    stderr: str
    '''错误错误内容'''
    returncode: int
    '''命令执行返回码'''


class SSHManager(SSHClient):
    def __init__(self):
        super().__init__()
        self.shell_config = None
        self.shell_ip = None
        self.shell_port = None
        self.shell_username = None
        self.shell_password = None
        self.set_missing_host_key_policy(AutoAddPolicy())

    @property
    def connection(self) -> SSHClient:
        '''SSH连接对象
        Returns:
            SSHClient: SSH连接对象
        '''
        if self.get_transport():
            return self
        return self._establish_connection()
    
    def _establish_connection(self) -> SSHClient:
        '''建立SSH连接
        Returns:
            SSHClient: SSH连接对象
        '''
        self.connect(self.shell_ip, port=self.shell_port, 
                     username=self.shell_username, password=self.shell_password)
        return self
    
    @connection.setter
    def connection(self, config: dict) -> SSHClient:
        '''重新设置属性连接
        Args:
            config (dict): SSH连接配置
        Returns:
            SSHClient: SSH连接对象
        '''
        if self.get_transport():
            self.close()

        required_keys = ["ip", "port", "username", "password"]
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ValueError(f"缺少SSH连接所需关键参数: {', '.join(missing_keys)}")

        self.shell_ip = config["ip"]
        self.shell_port = config["port"]
        self.shell_username = config["username"]
        self.shell_password = config["password"]

        return self._establish_connection()

    def disconnect(self):
        """主动关闭连接的方法"""
        self.close()

    def execute(self, cmd: str,timeout: int = 10) -> SSHCommandResult:
        """ssh执行函数

        Args:
            cmd (str): 执行命令
            timeout (int, optional): 执行超时时间. Defaults to 10.

        Returns:
            SSHCommandResult: 返回执行结果
        """
        if not self.get_transport():
            self.connection
            self.log_warning(f"当前ssh未连接执行时连接,连接设备:[{self.shell_ip}]", stack=3)
        stdin, stdout, stderr = self.exec_command(command=cmd, timeout=timeout)
        exit_status = stdout.channel.recv_exit_status()
        return SSHCommandResult(
            stdout=stdout.read().decode("utf-8").strip(),
            stderr=stderr.read().decode("utf-8").strip(),
            returncode=exit_status,
        )
