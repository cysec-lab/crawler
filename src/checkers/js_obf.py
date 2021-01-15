from __future__ import annotations, unicode_literals
import re
from enum import Enum, auto

class CheckObfResult(Enum):
    NORMAL = auto()
    RANDOM = auto()
    ENCODE = auto()

class CheckObf:
    """
    難読化の特徴を利用したドライブバイダウンロード攻撃検知方式の実装と評価
    https://ci.nii.ac.jp/naid/110010021487

    から実装、難読化検知を行う
    """
    def __init__(self, src: str) -> None:
        self.src = src
        self.alphabets = self.cul_char_by_re(r'[^a-zA-Z]')
        self.numbers   = self.cul_char_by_re(r'[^0-9]')
        self.symbols   = self.cul_char_by_re(r'[a-zA-Z0-9]')
        self.code_len  = self.check_chars_of_line()
        self.unique_chars = self.check_total_unique_chars()
        self.unique_words = self.check_total_unique_words()
        super().__init__()


    def check(self) -> CheckObfResult:
        """
        暗号化チェックを行う
        """
        if self.code_len < 400:
            # 400文字以下の文字列ならば暗号化されていない
            return CheckObfResult.NORMAL
        elif self.code_len < 2000:
            # 真ん中ルート
            if self.code_len / self.unique_chars < 200:
                return CheckObfResult.RANDOM
            elif self.unique_chars < self.unique_words:
                return CheckObfResult.RANDOM
            else:
                return CheckObfResult.ENCODE
        else:
            # 右ルート
            a_b = self.code_len / self.unique_chars
            if a_b < 10:
                return CheckObfResult.ENCODE
            elif a_b < 95:
                return CheckObfResult.RANDOM
            else:
                if self.unique_chars > self.unique_words:
                    return CheckObfResult.ENCODE
                else:
                    return CheckObfResult.RANDOM
                # return CheckObfResult.ENCODE


    def check_chars_of_line(self) -> int:
        """
        コードの中で1行あたりの文字列の長さが最長の長さを返す
        """
        splied = self.src.split('\n')
        # 各行長い列順にソート
        splied.sort(key = lambda s: len(s), reverse=True)
        return len(splied[0])


    def check_total_unique_chars(self) -> int:
        """
        [,;&]の文字数をカウント
        """
        return self.cul_char_by_re(r'[^,;&]')


    def check_total_unique_words(self) -> int:
        """
        [http, div, :]をカウント
        """
        unique_words = re.findall(r'(http|div|:)', self.src)
        return len(unique_words)

    def cul_char_by_re(self, regex: str) -> int:
        """
        指定された正規表現に当てはまる文字列をすべて消して残った文字数を返す
        """
        return len(re.sub(regex, '', self.src))