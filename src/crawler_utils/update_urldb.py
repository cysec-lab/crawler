from typing import Any, Set, List, Tuple

from check_allow_url import check_searched_url


def get_not_achieved_url(url_db: Any, assignment_url_set: Set[str], filtering_dict: Any) -> List[Tuple[str, str]]:
    """
    過去のクローリング結果と比較してまだクローリングしていないURLがあれば
    クローリングしていないURLをsetとして返す

    Args
    - url_db: dbm._Database
      - 過去のクローリングで取得したURLデータベース
    """
    url_set = set()
    filterd_list: List[Tuple[str, str]] = list()

    key = url_db.firstkey()
    while key is not None:
        content: str = url_db[key].decode("utf-8")
        if "True" in content:
            # url_dbからクローリングすべきurlたちをurl_db_setに追加する
            url: str = key.decode("utf-8")
            url_set.add(url)
        key = url_db.nextkey(key)

    # すでに探索したurlとurl_dbから取った探索すべきurlの差集合をとる
    not_achieved = url_set.difference(assignment_url_set)

    # フィルタリングする
    for url in not_achieved:
        if check_searched_url((url, "url_db"), 0, filtering_dict) == True:
            filterd_list.append((url, "url_db"))

    return filterd_list
