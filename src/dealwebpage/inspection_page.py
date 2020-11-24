from typing import Any, Dict, Iterable, Tuple, Union, cast
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from bs4.element import ResultSet

from dealwebpage.webpage import Page


def ston(string: str):
    """
    文字を数値に変える
    例：'20px' -> 20
    """
    if type(string) is str:
        if string.isdigit():
            return int(string)
        for s in string:
            if not s.isdigit():
                break
        re = string[0:string.find(s)] # type: ignore
        if re.isdigit():
            return int(re)
        else:
            return 0
    elif type(string) is int:
        return string
    elif type(string) is None:
        return 0
    else:
        return 0


def check_style(iframe_list: list[ResultSet]) -> Union[list[str], bool]:
    """
    widthとheightが設定されていなかったiframeの中から、
    さらにstyleにwidthとheightが設定されていないもの、visibility:hidden、display:noneが設定されているものを探す
    """
    inv = set()
    for iframe in iframe_list:
        style: str = iframe.get('style')
        if style:
            style = style.replace(' ', '')
            if ('width' not in style) and ('height' not in style):   # styleの中にwidthとheightの両方がなければ
                inv.add(iframe)
                continue
            elif ('visibility:hidden' in style) or ('display:none' in style):   # 見えないように設定されているか
                inv.add(iframe)
                continue
            temp = style.split(';')    # 分けてfor文で回す必要はないので改良の余地あり
            for attr in temp:
                if ('width' in attr) or ('height' in attr):   # styleのwidthとheightの値を取得
                    num = attr[attr.find(':')+1:]
                    if ston(num) == 1:
                        inv.add(iframe)
        else:
            inv.add(iframe)
    if inv:
        return list(inv)
    else:
        return False


def invisible(iframe_list: list[ResultSet]) -> Union[list[str], bool]:
    """
    display:none か visibility:hidden が設定されている
    width、height属性値が0か、または設定されていない場合、目に見えないと判定。
    """
    inv: list[ResultSet] = list()
    for iframe in iframe_list:
        width: str = iframe.get('width')
        height: str = iframe.get('height')
        style: str = iframe.get('style')
        if 'display:none' in style or 'visibility:hidden' in style:
            inv.append(iframe)
        else:
            if width or height:
                if ston(width) + ston(height) < 3:   # widthとheightの両方が1以下ならば
                    inv.append(iframe)
            else:
                # width か height が0のとき
                inv.append(iframe)
    if inv:
        re = check_style(inv)   # 簡単なstyleのチェック
        if re:
            return re   # それでも枠がないと判定されたら
        else:
            return False
    else:
        return False


def get_src_of_tag(tags: Iterable[ResultSet]) -> Union[list[str], bool]:
    """
    tagsのsrc属性値のURLのリストを返す
    src値がなければFalse
    """
    src_list: list[str] = list()
    for tag in tags:
        src: Any = tag.get('src')
        if src:
            src = cast(str, src)
            o = urlparse(src)
            tag_src_url = o.netloc + o.path
            src_list.append(tag_src_url)     # iframeとscriptタグのsrc値は、queryとfragmentを削除したURLを保存
    if src_list:
        return sorted(src_list)
    else:
        return False


def iframe_inspection(soup: BeautifulSoup) -> Union[bool, Dict[str, Union[bool, list[str]]]]:
    """
    iframeタグの検査
    iframeタグが見つからなければ、False
    見つかれば、[iframeのsrcのリスト or False]と[枠の設定が0のiframeのリスト or False]が返る
    """
    iframe_tags = soup.findAll('iframe')
    if len(iframe_tags) == 0:
        return False
    result: Dict[str, Union[bool, list[str]]] = dict()
    result['iframe_src_list'] = get_src_of_tag(iframe_tags)
    result['invisible_iframe_list'] = invisible(iframe_tags)
    return result


def str_mix_upper_lower(value: str) -> list[str]:
    """
    valueの文字列を大小全パターン返す
    例：ab なら ['Ab', 'AB', 'aB', 'ab']
    """
    value_low = value.lower()
    value_set = set()
    value_set.add(value_low)
    for i in range(len(value_low)):
        temp_value_set = set()
        for j in value_set:
            value2 = j[:i] + j[i].upper() + j[i + 1:]    # i番目だけを大文字に変える
            temp_value_set.add(value2)
            value2 = j[:i] + j[i].lower() + j[i + 1:]    # i番目だけを小文字に変える
            temp_value_set.add(value2)
        value_set = value_set.union(temp_value_set)
    return list(value_set)


def meta_refresh_inspection(soup: BeautifulSoup) -> Union[list[ResultSet], bool]:
    """
    metaセットの中で refresh を抽出してリストで返す
    """
    meta_refresh_list: list[ResultSet] = list()
    refresh_str_list: list[str] = str_mix_upper_lower('refresh') # HTML文は小文字大文字の区別がないため
    for i in refresh_str_list:
        if meta_refresh_list:
            meta_refresh_list.extend(soup.find_all('meta', attrs={'http-equiv': i}))
        else:
            meta_refresh_list = soup.find_all('meta', attrs={'http-equiv': i})
    if meta_refresh_list:
        return meta_refresh_list
    else:
        return False


def get_meta_refresh_url(meta_refresh_list: list[ResultSet], page: Page) -> set[str]:
    """
    meta-refresh の src を 正規化して返す
    """
    # 'URL'の文字の大文字小文字混ぜ合わせた全てのリストを得る
    url_str_list = str_mix_upper_lower('url')
    meta_refresh_url_list: set[str] = set()
    for meta_refresh in meta_refresh_list:
        meta_refresh_content: Any = meta_refresh.get('content')
        if not (meta_refresh_content is None):
            meta_refresh_content = meta_refresh_content.replace(' ', '')
            for url_str in url_str_list:
                url_start: int = meta_refresh_content.find(url_str)
                if not (url_start == -1):
                    meta_refresh_url = meta_refresh_content[url_start + 3:]
                    if not(meta_refresh_url.startswith('http')):
                        meta_refresh_url: str = page.comp_http(page.url, meta_refresh_url)
                    meta_refresh_url_list.add(meta_refresh_url)
    return meta_refresh_url_list


def script_name_inspection(script_tags: Iterable[ResultSet]) -> Union[bool, list[Tuple[str, str]]]:
    """
    スクリプトのsrc先のファイル名が1文字や特定ファイル名の場合、そのスクリプト名とscriptタグのリストを返す
    怪しいスクリプト名がなければ、Falseを返す
    """
    suspicious_names = {'ngg', 'script', 'js', 'ri'}   # 特定スクリプト名は関連研究の論文より参考
    script_names: list[Tuple[str, str]] = list()
    for script_tag in script_tags:
        script_src: ResultSet = script_tag.get('src')
        if script_src:
            slash: int = script_src.rfind('/')
            period: int = script_src.rfind('.')
            if period:
                script_name: str = script_src[slash + 1:period] # type: ignore
            else:
                script_name: str = script_src[slash + 1:] # type: ignore
            if len(script_name) < 2:
                script_names.append((script_name, str(script_tag)))   # スクリプト名が一文字
            if script_name in suspicious_names:
                script_names.append((script_name, str(script_tag)))   # スクリプト名が怪しい
    if script_names:
        return script_names
    else:
        return False


def title_inspection(soup: BeautifulSoup) -> Union[str, bool]:
    """
    titleタグ内にscriptタグが含まれているかどうか
    """
    if soup.title:
        title: str = soup.title.string
        if not(title is None):
            if '<script' in title:
                return title
            else:
                return False
    return False


# scriptタグの検査
# scriptタグが見つからなければ、Falseが返る
# 見つかれば、
def script_inspection(soup: BeautifulSoup):
    script_tags = soup.find_all('script')  # 要素の指定は大文字小文字を区別しなくてよい
    if len(script_tags) == 0:
        return False
    result: Dict[str, Union[str, bool, list[Tuple[str, str]], list[str]]] = dict()
    result['script_in_title'] = title_inspection(soup)   # titleにscriptが含まれていると怪しい (関連研究より
    result['suspicious_script_name'] = script_name_inspection(script_tags)   # script名の検査
    result['script_src_list'] = get_src_of_tag(script_tags)    # scriptのsrcURLを取得
    return result


def form_inspection(soup: BeautifulSoup) -> Union[bool, Dict[str, list[str]]]:
    """
    formのaction要素を返す
    """
    form_tags: ResultSet = soup.find_all("form")
    if len(form_tags) == 0:
        return False
    result: Dict[str, list[str]] = dict()
    result["form_action"] = list()
    for form_tag in form_tags: # type: ignore
        action_url: str = form_tag.get('action')
        if action_url:
            result["form_action"].append(action_url)

    if result["form_action"]:
        return result
    else:
        return False
