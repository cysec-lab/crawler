from __future__ import annotations

import re
from typing import List, Tuple
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from typing import Optional


def complete_url_by_html(html: str, url: str, html_special_char: List[Tuple[str, ...]]) -> str:
    """
    与えられたHTMLのscript>srcを修正して返す
    """
    soup = BeautifulSoup(html, 'html.parser')

    # 同じScriptが存在した場合に複数回replaceしないようにメモ
    memo = set()

    for sc in soup.findAll('script'): # type: ignore
            link_url: Optional[str] = sc.get('src')
            if link_url:
                js_url = complete_js_url(link_url, url, html_special_char)
                if not js_url in memo:
                    html = html.replace(link_url, js_url)
                memo.add(js_url)
    return html

rm_query = re.compile(r'(.+?)\?')

def remove_query(url: str) -> str:
    """
    クエリを取り除く
    """
    reg = rm_query.match(url)
    if reg:
        url = reg.groups()[0]
    if url.endswith('/'):
        url = url[:-1]
    return url


def remove_port(url: str) -> str:
    """
    ポートを取り除く
    """
    return re.sub(r':\d+', '', url)


def remove_scheme(url: str) -> str:
    """
    http:// とか https:// を削除する
    頭についているもののみを対象とする
    """
    if url.startswith('https://'):
        return url[8:]
    elif url.startswith('http://'):
        return url[7:]
    else:
        return url

def fix_request_url(url: str) -> str:
    """
    拡張機能からとったURLの修正を行う
    """
    fixed_url = remove_scheme(url)
    # www.google.com/url?sa=p&q= から始まる場合は以降のURLのみについて考える
    if fixed_url.startswith('www.google.com/url?sa=p&q='):
        fixed_url = remove_scheme(fixed_url[26:])
    return remove_query(fixed_url)


last_slash = re.compile(r'.+\/')

def complete_js_url(src_url: str, page_url: str, html_special_char: List[Tuple[str,...]]):
    """
    与えられたJSへのリンクsrcURLを補完する

    args:
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
    elif not src_url.startswith(('http', 'chrome', 'https')):
        # pageURL最後の/までのと与えられたURLをくっつける
        # すでにhttp:// から始まるURLまたは chrome://から始まるURLの場合は飛ばす
        # ex. chrome://browser/content/aboutNetError.js
        # Firefox の組み込みJS
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

    return remove_port(src_url)
