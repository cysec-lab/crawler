class Alert:
    """
    アラート記録プロセス(summarize_alert.py)に送るデータ構造

    Args:
    - url       : 立命館サイトかどうかで記録を分けるために必要
    - file_name : 保存先ファイル名
    - content   : 書き込む中身
    - label     : CSVラベル
    """

    def __init__(self, url: str, file_name: str, content: str, label: str):
        self.url = url
        self.file_name = file_name
        self.content = content
        self.label = label
