from inspect import currentframe
from os.path import basename

currentframe: type

def location():
    """
    呼び出し時のソースコードの行とファイル名などを表示
    """
    frame = currentframe().f_back
    return "Error ({}, {}, {}): ".format(basename(frame.f_code.co_filename), frame.f_code.co_name, frame.f_lineno)
