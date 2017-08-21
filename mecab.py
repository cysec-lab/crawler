import MeCab
import json
from bs4 import NavigableString, Comment, Declaration, Doctype
import unicodedata
import time
import os


# 以下3つの関数、ネットから取ってきたソース URL = http://d.hatena.ne.jp/s-yata/20100619/1276961636
# 不要な空白を取り除き，空行以外を返す．
def nonEmptyLines(text_target):
    for line in text_target.splitlines():
        line = ' '.join(line.split())
        if line:
            yield line


def getNavigableStrings(soup):
    if isinstance(soup, NavigableString):
        if type(soup) not in (Comment, Declaration, Doctype) and soup.strip():   # ここにDoctypeを追加
            yield soup
    elif soup.name not in ('script', 'style'):
        for c in soup.contents:
            for g in getNavigableStrings(c):
                if not ('<iframe' in g):
                    yield g


# 正規化の後で不要な空白・改行を取り除く．
def normalizeText(target_text):
    target_text = unicodedata.normalize('NFKC', target_text)
    return '\n'.join(nonEmptyLines(target_text))


def detect_hack(text):
    text = text.strip().replace(' ', '')     # 空白、改行を削除する
    result = 0
    while text:
        h = text.find('h')
        if h == -1:
            h = text.find('H')
            if h == -1:
                break
        h_area = text[h:h+10].lower()   # 'h'又は'H'が見つかってから10文字を取り、小文字にする
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


def get_tf_dict_by_mecab(soup):
    # HTML文のタグを除去
    text = '\n'.join(getNavigableStrings(soup))
    text = normalizeText(text)
    # hacked byの文字列を探す。「hack」が見つかれば1、「hacked」が見つかれば2、「hacked by」が見つかれば3とする。
    hack_level = detect_hack(text)

    # mecabで形態素解析
    """
    # windows.ver
    mecab_u_dic = ''
    file = os.listdir('../../../../ROD/mecab-dic/')
    for dic in file:
        if dic.endswith('.dic'):
            mecab_u_dic += '../../../../ROD/mecab-dic/' + dic + ','
    mecab_u_dic = mecab_u_dic.rstrip(',')
    # mecabで形態素解析
    try:
        mecab = MeCab.Tagger('-Ochasen -u ' + mecab_u_dic)
    except RuntimeError:
        time.sleep(1)
        try:
            mecab = MeCab.Tagger('-Ochasen -u ' + mecab_u_dic)
        except RuntimeError:
            return hack_level, False
    # linux.ver
    """
    try:
        mecab = MeCab.Tagger('-Ochasen -d /usr/lib/mecab/dic/mecab-ipadic-neologd')
    except RuntimeError:
        time.sleep(1)
        try:
            mecab = MeCab.Tagger('-Ochasen -d /usr/lib/mecab/dic/mecab-ipadic-neologd')
        except RuntimeError:
            return hack_level, False

    mecab.parse('')    # エラー回避のおまじない
    node = mecab.parseToNode(text)
    tf_dict = dict()
    word_counter = 0
    while node:
        kind = node.feature.split(',')[0]
        if kind == '名詞':
            word = node.surface
            if word.isdigit():    # 数字は無視
                node = node.next
                continue
            if len(word) == 1:   # str.isalpha()という英字を判別する関数があるが、なぜか漢字もTrueを返していた
                if ('a' <= word <= 'z') or ('A' <= word <= 'Z'):   # 英字一文字は無視
                    node = node.next
                    continue
            if 'http://' in word:  # http:// が頻発していたので消す
                node = node.next
                continue
            if word in tf_dict:
                tf_dict[word] += 1
            else:
                tf_dict[word] = 1
            word_counter += 1
        node = node.next
    if word_counter:
        # tf値計算
        for word, count in tf_dict.items():
            tf = count / word_counter
            tf_dict[word] = tf
        return hack_level, tf_dict
    else:
        return hack_level, False


def get_top10_tfidf(tfidf_dict):
    tfidf_list = sorted(tfidf_dict.items(), key=lambda x: x[0], reverse=False)   # 文字でソートする
    tfidf_list = sorted(tfidf_list, key=lambda x: x[1], reverse=True)            # tfidf値でソートし直す
    # 以上の処理で、tfidf値が高いもの順で、値が同じの場合は文字でソートされたリストが出来る
    top10 = list()
    for i in range(len(tfidf_list)):
        if i >= 10:
            break
        top10.append(tfidf_list[i][0])
    return top10


def make_tfidf_dict(idf_dict, tf_dict):
    tfidf_dict = dict()
    for word, tf in tf_dict.items():
        if word in idf_dict:
            tfidf = tf * idf_dict[word]
            tfidf_dict[word] = tfidf
        else:
            tfidf = tf * idf_dict['NULLnullNULL']
            tfidf_dict[word] = tfidf
    return tfidf_dict


def add_word_dic(src_dic, dic):
    for word in dic.keys():
        if word in src_dic:
            src_dic[word] += 1
        else:
            src_dic[word] = 1
    if 'NumOfPages' in src_dic:
        src_dic['NumOfPages'] += 1
    else:
        src_dic['NumOfPages'] = 1
    return src_dic


def save_dict(host, dic, dic_type):
    if len(dic_type) > 0:
        f = open('../../../../' + dic_type + '/' + host + '.json', 'w')
        json.dump(dic, f)
        f.close()

