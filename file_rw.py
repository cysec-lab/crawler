import json


def w_file(file_name, data, mode="w"):
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
    f = open(name + '.json', 'w')
    json.dump(data, f)
    f.close()


def r_json(name):
    f = open(name + '.json', 'r')
    data = json.load(f)
    f.close()
    return data
