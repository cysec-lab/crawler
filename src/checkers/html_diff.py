import difflib
from typing import List, Tuple

class Difference:
    def __init__(self, differ, fromlines, tolines) -> None:
        self.differ: str = differ
        self.fromlines: List[str] = fromlines
        self.tolines: List[str] = tolines

    def __repr__(self) -> str:
        res = []
        res.append(self.differ)
        [res.append(text) for text in self.fromlines]
        [res.append(text) for text in self.tolines]
        return str(res)

    def data(self) -> Tuple[str, List[str], List[str]]:
        return (self.differ, self.fromlines, self.tolines)

def differ(html1, html2) -> List[Difference]:
    """
    差分を取って変更があったところだけを変更点をリストで返す
    """
    diff = difflib.Differ().compare(html1, html2)
    list_diff = list(diff)
    res = []

    print(html1)
    print(html2)

    i = 0
    while i < len(list_diff):
        # 削除はこの際問題にならないので気にしない
        if list_diff[i].startswith('-'):
            # 変更された行数を数える
            del_num = 0
            mod_flag = False
            guide_flag = False
            fromlines = []
            tolines = []
            while list_diff[i].startswith('-'):
                mod_flag = True
                fromlines.append(list_diff[i][2:])
                del_num += 1
                i += 1
            while i < len(list_diff) and list_diff[i].startswith('?'):
                # 差異を教えてくれる行がある時がある
                if len(list_diff[i]) > 3:
                    start = 2
                    while list_diff[i][start] == ' ':
                        start += 1
                    last = len(list_diff[i]) - 1
                    while list_diff[i][last] == ' ':
                        last -= 1
                    start -= 2
                    last -= 2
                    guide_flag = True
                i += 1
            while i < len(list_diff) and list_diff[i].startswith('+') and del_num > 0:
                # 変更行分までは変更として扱う
                tolines.append(list_diff[i][2:])
                del_num -= 1
                i += 1
            if mod_flag:
                if del_num == 0:
                    if guide_flag:
                        fromlines = [''.join(fromlines[0][start:last])]
                        tolines = [''.join(tolines[0][start:last])]
                    res.append(Difference('modified', fromlines, tolines))
                else:
                    res.append(Difference('delete', fromlines, tolines))
                mod_flag = False

        if i < len(list_diff) and list_diff[i].startswith('+'):
            fromlines = []
            while list_diff[i].startswith('+'):
                fromlines.append(list_diff[i][2:])
                i += 1
            res.append(Difference('add', fromlines, []))
            i -= 1
        i += 1
    return res
