import json


def w_file(name, data):
    try:
        with open(name, 'w', encoding='utf-8') as f:
            f.write(data)
    except:
        try:
            with open(name, 'w', encoding='shift-jis') as f:
                f.write(data)
        except:
            raise


def wa_file(name, data):
    try:
        with open(name, 'a', encoding='utf-8') as f:
            f.write(data)
    except:
        try:
            with open(name, 'a', encoding='shift-jis') as f:
                f.write(data)
        except:
            raise


def r_file(name, mode='r'):
    try:
        with open(name, mode) as f:
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
