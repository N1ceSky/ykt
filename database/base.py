import re

import requests

URL = "http://122.51.89.123/tiku/api/v1"


def format_string(string):
    string = string.translate(
        str.maketrans(
            {
                12288: 32,  # 全角空格转半角空格
                65281: 40,  # 全角感叹号转半角感叹号
                65282: 41,  # 全角问号转半角问号
                65288: 46,  # 全角句号转半角句号
                65292: 44,  # 全角逗号转半角逗号
                65306: 58,  # 全角冒号转半角冒号
                65311: 63,  # 全角问号转半角问号
                65317: 59,  # 全角分号转半角分号
                12289: 46,  # 另一种全角句号转半角句号
                65284: 39,  # 全角撇号转半角撇号
                65285: 39,  # 另一种全角撇号转半角撇号
                65286: 34,  # 全角双引号转半角双引号
                65287: 34,  # 另一种全角双引号转半角双引号
            }
        )
    )
    string = re.sub(r"\s+", " ", string)
    # 替换中文引号为英文引号
    string = re.sub(r"[“”]", '"', string)
    string = re.sub(r"[‘’]", "'", string)
    # 替换中文句号为英文句号
    string = re.sub(r"。", ".", string)
    while string and string[-1] in ".,;:!?。：、，；！？":
        string = string[:-1]

    return string.strip()


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
