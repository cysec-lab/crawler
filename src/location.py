from inspect import currentframe
from os.path import basename


# この関数を呼び出すと、呼び出した時のソースコードの行とファイル名などを表示する。
def location():
    frame = currentframe().f_back
    return "Error ({}, {}, {}): ".format(basename(frame.f_code.co_filename), frame.f_code.co_name, frame.f_lineno)
