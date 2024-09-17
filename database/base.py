import sqlite3

from .common import DATABASE_PATH


class YKTBase:
    """YKT数据库"""

    def __init__(self) -> None:
        self.connect = sqlite3.connect(DATABASE_PATH)  # 连接数据库，没有就创建
        self.cursor = self.connect.cursor()  # 获取游标

    def search(self, question, table="QUIZ"):
        """
        查询表中给定question对应的answer。

        :param question: 需要查询的问题
        :return: 如果找到答案则返回答案，否则返回None
        """
        self.cursor.execute(
            f"SELECT answer FROM {table} WHERE question LIKE ?", (question,)
        )
        result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

    def submit(self, question, answer, table="QUIZ"):
        # 创建表单并添加数据
        self.cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {table} (question TEXT PRIMARY KEY NOT NULL, answer TEXT NOT NULL);"
        )

        self.cursor.execute(
            f"insert or ignore into {table} (question,answer) values (?,?)",
            (question, answer),
        )

        # self.cursor.close()
        self.connect.commit()  # 提交更改

    def printAllCaptcha(self):
        # 查询CAPTCHA表下全部数据并输出
        for question, answer in self.cursor.execute("select * from CAPTCHA").fetchall():
            print(question, answer)

    def length(self, table="CAPTCHA"):
        # 使用 COUNT(*) 来计算表中的所有行
        self.cursor.execute(f"SELECT COUNT(*) FROM {table};")
        # 获取结果
        count = self.cursor.fetchone()[0]
        return count

    def close(self):
        self.cursor.close()  # 关闭游标
        self.connect.close()  # 关闭数据库连接
