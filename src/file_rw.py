import json

def w_file(file_name, data, mode="w"):
    """
    エンコード方式を指定してデータを書き込む
    エラーが出てもそのまま書き込みを継続する

    args:
        file_name: ファイル名
        data: 書き込み内容
    """
    enc_list = ["utf-8", "shift_jis", "cp932", "iso-2022-jp"]
    for enc in enc_list:
        with open(file_name, mode=mode, encoding=enc) as f:
            try:
                f.write(data)
            except UnicodeDecodeError:
                continue
            except UnicodeEncodeError:
                continue
            else:
                break


def r_file(name, mode="r"):
    """
    文字列読み取り
    エラーが出ても読み取り続ける

    args:
        name: 読み取りファイル名
    """
    enc_list = ["utf-8", "shift_jis", "cp932", "iso-2022-jp"]
    for enc in enc_list:
        with open(name, mode=mode, encoding=enc) as f:
            try:
                read = f.read()     # 改行文字は含まれる
            except UnicodeDecodeError:
                continue
            except UnicodeEncodeError:
                continue
            else:
                return read
    return None


def w_json(name, data):
    """
    データを.jsonで保存する

    args:
        name: ファイル名(拡張子なし)
        data: データ
    """
    f = open(name + '.json', 'w')
    json.dump(data, f)
    f.close()


def r_json(name):
    """
    jsonデータ読み出し

    args:
        name: ファイル名(拡張子なし)
    """
    f = open(name + '.json', 'r')
    data = json.load(f)
    f.close()
    return data
