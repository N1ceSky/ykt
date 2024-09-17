import pickle
from pathlib import Path

from prettytable import PLAIN_COLUMNS, PrettyTable

ROOT_PATH = Path.cwd() / "cookies"


class CookiesManager:
    """cookies管理器"""

    # cookies索引
    index = -1

    def __init__(self) -> None:
        self.fname = "cookies.pkl"
        self.allUser = [p for p in ROOT_PATH.glob("*") if p.is_dir()]

    @property
    def cookies(self):
        """当前选择的cookies"""
        if self.index >= 0:
            path = self.allUser[self.index] / self.fname
            if path.exists():
                with open(path, "rb") as f:
                    cookies = pickle.load(f)
                return cookies
        return None

    @property
    def name(self):
        """当前选择的账号名"""
        if self.index >= 0:
            return self.allUser[self.index].name
        else:
            return ""

    @property
    def expires_time(self):
        if self.cookies:
            return min([coo.expires for coo in self.cookies if coo.expires])
        else:
            return 0

    def choice(self):
        """打印并选择账户"""
        # 打印
        self.print()
        # 选择
        if len(self.allUser) > 1:
            while True:
                try:
                    self.index = int(input("请选择账号："))
                except Exception:
                    break
                if self.index >= 0 and self.index < len(self.allUser):
                    break
        elif len(self.allUser) == 1:
            self.index = 0

    def print(self):
        table = PrettyTable()
        table.field_names = ["#", "账号"]
        for index, user in enumerate(self.allUser):
            table.add_row([index, user.name])
        table.set_style(PLAIN_COLUMNS)
        print("\n" + table.get_string() + "\n")

    def save(self, name, cookies):
        """保存传入的cookies"""
        path = ROOT_PATH / name
        path.mkdir(parents=True, exist_ok=True)
        with open(path / self.fname, "wb") as f:
            pickle.dump(cookies, f)


if __name__ == "__main__":
    manager = CookiesManager()
    manager.choice()
