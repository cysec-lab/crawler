import MeCab
import os
from mecab import getNavigableStrings, normalizeText
from bs4 import BeautifulSoup


def get_mecab(mecab_dic_path):
    # mecab辞書をインポート
    mecab_u_dic = ''
    file = os.listdir(mecab_dic_path)
    for dic in file:
        if dic.endswith('.dic'):
            mecab_u_dic += mecab_dic_path + dic + ','
    mecab_u_dic = mecab_u_dic.rstrip(',')
    mecab = MeCab.Tagger('-Ochasen -u ' + mecab_u_dic)
    mecab.parse('')  # エラー回避のおまじない
    return mecab


def get_text(html):
    soup = BeautifulSoup(html, 'lxml')
    # HTML文のタグを除去
    text = '\n'.join(getNavigableStrings(soup))
    text = normalizeText(text)
    return text


def main():
    mecab = get_mecab('../ROD/mecab-dic/')

    text = '日本基礎心理学会第36回大会'

    node = mecab.parseToNode(text)
    while node:
        kind = node.feature.split(',')[0]
        if kind == '名詞':
            word = node.surface
            if word.isdigit():  # 数字は無視
                node = node.next
                continue
            if len(word) == 1:  # str.isalpha()という英字を判別する関数があるが、なぜか漢字もTrueを返していた
                if ('a' <= word <= 'z') or ('A' <= word <= 'Z'):  # 英字一文字は無視
                    node = node.next
                    continue
            if 'http://' in word:  # http:// が頻発していたので消す
                node = node.next
                continue
            print(word)
        node = node.next


if __name__ == '__main__':
    main()
