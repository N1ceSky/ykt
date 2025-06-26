import sys

import requests
import toml

try:
    URL = toml.load("./config.toml")["tiku"]["url"]
    assert URL, "无效的题库url"
except Exception:
    print("无效的题库url")
    sys.exit()


class YKTBase:
    """YKT数据库"""

    def __init__(self) -> None:
        self.url = URL

    @property
    def headers(self):
        return {
            "authorization": "esqxlRkSQsfCJ95KTkKu",
            "Content-Type": "application/json",
        }

    def search(self, question):
        """
        查询

        :param question: 需要查询的问题
        :return: 如果找到答案则返回答案，否则返回None
        """
        data = {"question": question}
        res = requests.post(f"{self.url}/query", headers=self.headers, json=data).json()
        # none或答案
        return res["data"]["answer"]

    def submit(self, question, answer):
        data = {"question": question, "answer": answer}
        requests.post(f"{self.url}/submit", headers=self.headers, json=data)

    def searchDiss(self, question):
        """
        查询

        :param question: 需要查询的问题
        :return: 如果找到答案则返回答案，否则返回None
        """
        data = {"question": question}
        res = requests.post(
            f"{self.url}/querydiss", headers=self.headers, json=data
        ).json()
        # none或答案
        return res["data"]["answer"]

    def submitDiss(self, question, answer):
        data = {"question": question, "answer": answer}
        requests.post(f"{self.url}/submitdiss", headers=self.headers, json=data)
        data = {"question": question, "answer": answer}
        requests.post(f"{self.url}/submitdiss", headers=self.headers, json=data)
