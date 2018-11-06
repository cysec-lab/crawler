from inspect import currentframe
from os.path import basename


def location():
    frame = currentframe().f_back
    return "Error ({}, {}, {}): ".format(basename(frame.f_code.co_filename), frame.f_code.co_name, frame.f_lineno)
