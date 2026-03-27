__version__ = "1.0.0"

from scripts.abstract import abstract


class Test(abstract):
    def __init__(self):
        super().__init__()
        

    def test_command(self,command:str):
        self.execute(command)
        self.log_info(f"测试{command}命令，结果：{self.execute(command)}")

if __name__ == "__main__":
    test = Test()
    test.test_command("cat test.txt")