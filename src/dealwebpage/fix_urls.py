from __future__ import annotations

import re
from typing import List, Tuple
from urllib.parse import urlparse

last_slash = re.compile(r'.+\/')

def complete_js_url(src_url: str, page_url: str, html_special_char: List[Tuple[str,...]]):
    """
    与えられたJSファイルへのsrcURLを補完する

    - args:
      - src_url: <script src=HOGEHOGE> のHOGEHOGE
      - page_url: scriptURLを見つけたページのURL
    """
    parsed = urlparse(page_url)

    if src_url.startswith('//'):
        # // から始まる場合はhttp:を補完
        tmp = parsed.scheme + ':' + src_url
        src_url = tmp
    elif src_url.startswith('/'):
        # / から始まる場合はホスト名を補完
        tmp = parsed.scheme + '://' + parsed.netloc + src_url
        src_url = tmp
    elif src_url.startswith('..'):
        # pageURL最後の/までのと与えられたURLをくっつける
        while_slash = last_slash.match(page_url)
        if while_slash:
            tmp = while_slash[0] + src_url
            src_url = tmp

    if '..' in src_url:
        # ../を消す
        parsrc = urlparse(src_url)
        div = parsrc.path.split('/')
        res = []
        for d in div:
            if d != '..':
                res.append(d)
            else:
                res.pop()
        src_url = parsrc.scheme + '://' + parsrc.netloc + '/'.join(res)

    # 文字列置換
    src_url = src_url.replace('/./', '/')
    spechars = [spechar for spechar in html_special_char if spechar[0] in src_url]
    for spechar in spechars:
        src_url = src_url.replace(spechar[0], spechar[1])

    return src_url
