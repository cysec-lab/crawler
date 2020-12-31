from __future__ import annotations

from logging import Logger
from typing import Union

from dealwebpage.webpage import Page


def page_or_file(page: Page, logger: Logger) -> Union[str, bool]:
    """
    ページの content_type を調査
    content-type は長い場合があるのでどれか文字列中に含まれていないか全部見る
    ex 'text/html; charset=urf-8'

    args:
        page: 調査中のPage情報
    return:
        文字列(xml, html, js) or False
    """
    xml_types = ['plain/xml', 'text/xml', 'application/xml']
    html_types = ['html']
    js_types = [
        'application/javascript',
        'application/ecmascript',
        'application/x-ecmascript',
        'application/x-javascript',
        'text/javascript',
        # 'text/javascript1.0',
        # 'text/javascript1.1',
        # 'text/javascript1.2',
        # 'text/javascript1.3',
        # 'text/javascript1.4',
        # 'text/javascript1.5',
        'text/ecmascript',
        'text/jscript',
        'text/livescript',
        'text/x-ecmascript',
        'text/x-javascript'
    ]

    if page.content_type:
        for xml in xml_types:
            if xml in page.content_type:
                return 'xml'
        for html in html_types:
            if html in page.content_type:
                return 'html'
        for js in js_types:
            if js in page.content_type:
                return 'js'
        # 空白のままを含む不明な content_type ならば False
        logger.debug("Unkown content type: '%s'", page.content_type)
        return False
    else:
        # Content_type が None ならば
        return False


def check_redirect(page: Page, host: str):
    """
    リダイレクト先の調査
    - URLが変わっていなければFalse
    - リダイレクトしていても同じサーバ内ならば'same'
    - 違うサーバならTrue

    args:
        page: WebPageクラス
        host:
    return:
        文字列 or bool
    """
    if page.url_initial == page.url:
        return False
    if host == page.hostName:
        return 'same'
    return True
