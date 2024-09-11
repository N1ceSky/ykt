import hashlib
import io
import json

import requests
from bs4 import BeautifulSoup
from fontTools.ttLib import TTFont

from common import get_glyph_path

cache = {}


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

    cache[ttf_url] = table


def get_encrypt_string(htmlStr, ttf_url, sourceTable):
    if ttf_url not in cache:
        gen_table(ttf_url, sourceTable)

    soup = BeautifulSoup(htmlStr, "html.parser")
    str = soup.text
    encodeTags = soup.find_all("span", class_="xuetangx-com-encrypted-font")
    for encTag in encodeTags:
        dec_str = "".join(
            chr(cache[ttf_url].get(ord(c), c))  # 如果找不到对应的MD5，则保持原样
            for c in encTag.text
        )
        str = str.replace(encTag.text, dec_str)

    return format_string(str)


def format_string(str):
    return str.strip()


# 示例使用
with open("table.json", "r", encoding="utf-8") as f:
    source_table = json.loads(f.read())

ttf_url = "https://fe-static-yuketang.yuketang.cn/fe_font/product/exam_font_406141f644fa4418843e43aba5cc6ae5.ttf"
input_str = """<p><span class="xuetangx-com-encrypted-font">盾五脏老修际子转剂格随词方肝</span>？<br/></p>"""
result = get_encrypt_string(input_str, ttf_url, source_table)
print(result)
input_str = """<p><span style="font-size:10.5pt;mso-bidi-font-size:11.0pt;&#10;font-family:等线;mso-ascii-theme-font:minor-latin;mso-fareast-theme-font:minor-fareast;&#10;mso-hansi-theme-font:minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;&#10;mso-bidi-theme-font:minor-bidi;mso-ansi-language:EN-US;mso-fareast-language:&#10;ZH-CN;mso-bidi-language:AR-SA"><span class="xuetangx-com-encrypted-font">单使剂胃</span><span class="xuetangx-com-encrypted-font">肌间肌面随票右那凝到</span>？</span></p>"""
result = get_encrypt_string(input_str, ttf_url, source_table)
print(result)
input_str = """<p><strong><span style="font-size:10.5pt;mso-bidi-font-size:11.0pt;&#10;font-family:等线;mso-ascii-theme-font:minor-latin;mso-fareast-theme-font:minor-fareast;&#10;mso-hansi-theme-font:minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;&#10;mso-bidi-theme-font:minor-bidi;mso-ansi-language:EN-US;mso-fareast-language:&#10;ZH-CN;mso-bidi-language:AR-SA"><span class="xuetangx-com-encrypted-font">互板促汽那凝到</span>？</span></strong></p>"""
result = get_encrypt_string(input_str, ttf_url, source_table)
print(result)
input_str = """<p><span style="font-size:10.5pt;mso-bidi-font-size:11.0pt;&#10;font-family:等线;mso-ascii-theme-font:minor-latin;mso-fareast-theme-font:minor-fareast;&#10;mso-hansi-theme-font:minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;&#10;mso-bidi-theme-font:minor-bidi;mso-ansi-language:EN-US;mso-fareast-language:&#10;ZH-CN;mso-bidi-language:AR-SA"><span class="xuetangx-com-encrypted-font">针随其住减方留间</span>？</span></p>"""
result = get_encrypt_string(input_str, ttf_url, source_table)
print(result)
