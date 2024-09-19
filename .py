from bs4 import BeautifulSoup


def html2Str(htmlStr):
    soup = BeautifulSoup(htmlStr, "html.parser")
    texts = [text.strip() for text in soup.stripped_strings]
    return "\n".join(texts)


html = """
<div class="custom_ueditor_cn_body"><ol class=" list-paddingleft-2" style="list-style-type: decimal;"><li><p>&nbsp;<span style="color: #18191B; font-family: &quot;Arial Unicode MS&quot;; font-size: 18px; -webkit-text-stroke-color: #18191B; background-color: #FFFFFF;">请写下亲密关系能满足的你的3-5个需要。例如，亲密需要。</span></p></li><li><p><span style="color: #18191B; font-family: &quot;Arial Unicode MS&quot;; font-size: 18px; -webkit-text-stroke-color: #18191B; background-color: #FFFFFF;">上面的回答中，哪些是身体、心理、社会或生存需要？</span><br/></p></li></ol></div>
"""
c = html2Str(html)
print(c)
