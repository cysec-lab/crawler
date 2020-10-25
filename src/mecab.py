import time
import unicodedata
from typing import Any, Dict, List, Tuple, Union

import MeCab
from bs4 import BeautifulSoup, Comment, Declaration, Doctype, NavigableString


def nonEmptyLines(text_target: str):
    """
    不要な空白を取り除き，空行以外を返す．
    """
    for line in text_target.splitlines():
        line = ' '.join(line.split())
        if line:
            yield line


def getNavigableStrings(soup: Any) -> Any:
    """
    soupのオブジェクトに沿って文字列を返すように調整
    args:
        soup: soupオブジェクト
    return:
        必要とされるsoupオブジェクトのみを返す
    """
    if isinstance(soup, NavigableString):
        if type(soup) not in (Comment, Declaration, Doctype) and soup.strip():   # ここにDoctypeを追加
            yield soup
    elif soup.name not in ('script', 'style', 'title'):  # titleを追加
        for c in soup.contents:
            for g in getNavigableStrings(c):
                if not ('<iframe' in g):
                    yield g


def normalizeText(target_text: str) -> str:
    """
    正規化の後に nonEmptyLines()を呼び出して不要な空白, 改行を取り除く
    """
    target_text = unicodedata.normalize('NFKC', target_text)
    return '\n'.join(nonEmptyLines(target_text))


def detect_hack(text: str) -> int:
    """
    Hackの文字列を見つける
    hackレベルは "hack" が見つかれば1, "hacked" が見つかれば2, "hacked by" が見つかれば3

    args:
        text: 文字列
    return:
        result: hackレベル
    """
    text = text.strip().replace(' ', '')     # 空白、改行を削除する
    result = 0
    while text:
        h = text.find('h')
        if h == -1:
            h = text.find('H')
            if h == -1:
                break
        h_area = text[h:h+30].lower()   # 'h'又は'H'が見つかってから30文字を取り、小文字にする
        if 'hackedby' in h_area:
            result = 3
        elif 'hacked' in h_area:
            if result < 2:
                result = 2
        elif 'hack' in h_area:
            if result == 0:
                result = 1
        text = text[h+1:]
    return result


def get_tf_dict_by_mecab(soup: BeautifulSoup) -> Tuple[int, Union[bool, Dict[str, float]]]:
    """
    MeCabで形態素解析を行い辞書を作成する
    args:
        soup: 
    return:
        hacklevel: Hackedの文字列レベル
        ?tf_dict: 出現文字の辞書(文字列, tf値)
    """

    # HTML文のタグを除去(タイトルのcontentも削除)
    text = '\n'.join(getNavigableStrings(soup))
    text = normalizeText(text)
    hack_level = detect_hack(text)

    # mecabで形態素解析
    try:
        mecab: MeCab.Tagger = MeCab.Tagger('-d /usr/local/lib/mecab/dic/mecab-ipadic-neologd') # ('-Ochasen')
    except RuntimeError:
        time.sleep(1)
        try:
            mecab: MeCab.Tagger = MeCab.Tagger('-d /usr/local/lib/mecab/dic/mecab-ipadic-neologd') # ('-Ochasen')
        except RuntimeError:
            return hack_level, False

    # エラー回避用おまじない
    mecab.parse('')
    # textに対して形態素解析を実行
    node: Any = mecab.parseToNode(text)
    tf_dict: Dict[str, float] = dict()
    word_counter = 0
    # 辞書に名刺を追加していく
    while node:
        kind = node.feature.split(',')[0]
        if kind == '名詞':
            word = node.surface

            # 無視するものたち
            # 数字, "http://", 英字1文字
            if word.isdigit():
                node = node.next
                continue
            if len(word) == 1:
                # str.isalpha()という英字を判別する関数があるが、なぜか漢字もTrueを返していた
                if ('a' <= word <= 'z') or ('A' <= word <= 'Z'):
                    node = node.next
                    continue
            if 'http://' in word:
                node = node.next
                continue

            # 辞書に文字列が存在していなければ追加
            # すでに存在していればカウントを増やす
            if word in tf_dict:
                tf_dict[word] += 1
            else:
                tf_dict[word] = 1
            word_counter += 1
        node = node.next

    # 辞書に文字列が含まれているならばtf値を計算
    # 辞書のvalueを数え上げからtf値に変換
    if word_counter:
        for word, count in tf_dict.items():
            tf = count / word_counter
            tf_dict[word] = tf
        return hack_level, tf_dict
    else:
        return hack_level, False


def get_top10_tfidf(tfidf_dict: Dict[str, float], nth: Any) -> List[str]:
    """
    tfidfの辞書からトップ10を取り出す関数

    args:
        tfidf_dict: 単語の重要度が記載された辞書
        nth: ToDo これはなに
    return:
        top10: tf-idfが大きいものトップ10のリスト
    """

    # 文字列ソート
    tfidf_list = sorted(tfidf_dict.items(), key=lambda x: x[0], reverse=False)
    # tf-idf値でソート
    tfidf_list = sorted(tfidf_list, key=lambda x: x[1], reverse=True)
    # → tf-idf値が高いもの順, 値が同じの場合は文字でソートされたリスト

    # ToDo: refact
    top10: list[str] = list()
    tmp: list[Tuple[str, float]] = list()
    for i in range(len(tfidf_list)):
        if i >= 10:
            break

        tmp.append(tfidf_list[i])
        top10.append(tfidf_list[i][0])

    return top10


def make_tfidf_dict(idf_dict: Dict[str, int], tf_dict: Dict[str, float]) -> Dict[str, float]:
    """
    tf-idf辞書を作成する

    args:
        idf_dict: 各サーバにおいて現れる語それぞれの重み
        tf_dict: 各サーバにおける文字列の出現頻度辞書
    retrun:
        tfidf_dict: valueが重要度の単語辞書を作成
    """

    tfidf_dict: Dict[str, float] = dict()
    for word, tf in tf_dict.items():
        if word in idf_dict:
            tfidf = tf * idf_dict[word]
            tfidf_dict[word] = tfidf
        else:
            tfidf = tf * idf_dict['NULLnullNULL']
            tfidf_dict[word] = tfidf
    return tfidf_dict


def add_word_dic(src_dic: Dict[str, int], dic: Dict[str, float]):
    """
    Webサーバごとの辞書を各サイトの辞書をもとにアップデートする

    args:
        src_dict: 各サーバの辞書
        dic: 各サイトのtf辞書
    return:
        src_dict: サイトの辞書分の単語が追加された辞書
    """

    for word in dic.keys():
        if word in src_dic:
            src_dic[word] += 1
        else:
            src_dic[word] = 1

    # サーバ辞書内の総ページ数を更新する
    if 'NumOfPages' in src_dic:
        src_dic['NumOfPages'] += 1
    else:
        src_dic['NumOfPages'] = 1
    return src_dic


# def save_dict(host, dic, dic_type):
#     """
#     サイトに対して作成した文字列辞書を保存する

#     Args:
#         host: 調べたサイトのホスト名
#         dic: 形態素解析によって得られた文字列辞書
#         dic_type: 
#     """
#     if len(dic_type) > 0:
#         f = open('../../../../' + dic_type + '/' + host + '.json', 'w')
#         json.dump(dic, f)
#         f.close()
