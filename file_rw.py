import json


def w_file(file_name, data, mode="w"):
    try:
        f = open(file_name, mode=mode, encoding='utf-8')
        f.write(data)
        f.close()
    except:
        try:
            f.close()
        except:
            pass
        try:
            f = open(file_name, mode=mode, encoding='shift-jis')
            f.write(data)
            f.close()
        except:
            try:
                f.close()
            except:
                pass
            raise


def r_file(name, mode='r', encode='utf-8'):
    try:
        with open(name, mode, encoding=encode) as f:
            return f.read()     # 改行文字は含まれる
    except:
        raise


def w_json(name, data):
    f = open(name + '.json', 'w')
    json.dump(data, f)
    f.close()


def r_json(name):
    f = open(name + '.json', 'r')
    data = json.load(f)
    f.close()
    return data
