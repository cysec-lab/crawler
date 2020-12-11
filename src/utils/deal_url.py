import re
from typing import Any, Optional


def create_only_dict(regex_list: Any) -> Optional[re.Pattern[str]]:
    """
    フィルタに "ONLY.json" があった場合、
    中のリストから正規表現パターンを作成する

    input
    - regex_list: jsonから読み出した正規表現のリスト
      - {"Regex": [regex1, regex2....]}

    output
    - Pattern: 正規表現のコンパイル済みパターン
      - (regex1|regex2|....)
    """

    if "Regex" in regex_list and len(regex_list["Regex"]) > 0:
      regex = '(' + '|'.join(regex_list["Regex"]) + ')'
      print('regex: ' + regex)
      return re.compile(regex)
    else:
      return None
