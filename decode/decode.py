import hashlib
import io
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from fontTools.ttLib import TTFont

from .common import get_glyph_path

cache = {}

with open(Path.cwd() / "decode" / "table.json", "r", encoding="utf-8") as f:
    source_table = json.loads(f.read())


def gen_table(ttfUrl, sourceTable):
    """生成加密字体和原字体映射表"""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
    }
    response = requests.get(ttfUrl, headers=headers)
    response.raise_for_status()  # 确保请求成功
    font = TTFont(io.BytesIO(response.content))

    glyphset = font.getGlyphSet()
    table = {}
    for i in range(19968, 40870):
        unicode = font.getBestCmap().get(i)
        if unicode is not None:
            path = get_glyph_path(glyphset, unicode)
            if path is not None:
                path_str = json.dumps(path)
                # 加密字号转原字号
                table[i] = sourceTable[hashlib.md5(path_str.encode()).hexdigest()]
    cache[ttfUrl] = table


def format_string(string):
    string = re.sub(r"\s{2,}", " ", string)
    # 替换中文引号为英文引号
    string = re.sub(r"[“”]", '"', string)
    string = re.sub(r"[‘’]", "'", string)
    string = (
        string.replace("（", "(")
        .replace("）", ")")
        .replace("。", ".")
        .replace("，", ",")
        .replace("：", ":")
        .replace("；", ";")
        .replace("！", "!")
        .replace("？", "?")
    )
    while string and string[-1] in ".,;:!?、":
        string = string[:-1]
    return string.strip()


def decrypt(htmlStr, ttf_url, sourceTable=source_table):
    if ttf_url not in cache:
        gen_table(ttf_url, sourceTable)

    soup = BeautifulSoup(htmlStr, "html.parser")
    decryptStrs = []
    encodeTags = soup.find_all("span", class_="xuetangx-com-encrypted-font")
    # 标签泄露可能多导致tags内还有span标签 这里只取内容的第一项 第一项一定是一个加密字符串
    encodeStr = [span.contents[0] for span in encodeTags]
    for text in soup.stripped_strings:
        if text in encodeStr:
            decryptStrs.append(
                "".join([chr(cache[ttf_url].get(ord(c), c)) for c in text])
            )
        else:
            decryptStrs.append(text)

    return format_string("".join(decryptStrs))
