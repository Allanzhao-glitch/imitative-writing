__version__ = "1.0.0"

from scripts.abstract import abstract


class Test(abstract):
    def __init__(self):
        super().__init__()
        

    def test_command(self, command: str):
        result = self.execute(command)
        status = "✅ 成功" if result.returncode == 0 else "❌ 失败"
        self.log_info(f"命令: {command}")
        self.log_info(f"状态: {status} (返回码: {result.returncode})")
        if result.stdout:
            self.log_info(f"输出:\n{result.stdout}")
        if result.stderr:
            self.log_warning(f"错误:\n{result.stderr}")


if __name__ == "__main__":
    test = Test()
    test.test_command("ls -l")