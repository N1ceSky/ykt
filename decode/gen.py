"""根据原字体生成原始的table.json文件"""

import hashlib
import json

from fontTools.ttLib import TTFont

from common import get_glyph_path

font = TTFont("./SourceHanSansSC-VF.ttf")

glyphset = font.getGlyphSet()
table = {}
for i in range(19968, 40870):
    unicode = font.getBestCmap().get(i)
    if unicode is not None:
        path = get_glyph_path(glyphset, unicode)
        if path is not None:
            path_str = json.dumps(path)
            table[hashlib.md5(path_str.encode()).hexdigest()] = i


with open("table.json", "w", encoding="utf-8") as f:
    json.dump(table, f)
