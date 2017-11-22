import dbm
import time
import os
import json


if __name__ == '__main__':

    url_db = dbm.open('ROD/url_db', 'r')

    print(len(url_db))
    eight = 0
    seven = 0
    six = 0
    nine = 0

    for key in url_db.keys():
        value = url_db[key].decode('utf-8')
        flag = value[0:value.find(',')]
        n = value[value.find(',') + 1:]

        if n == '8':
            eight += 1
        elif n == '7':
            seven += 1
        elif n == '6':
            six += 1
        else:
            nine += 1

        print(flag)


    print(nine,eight, seven, six)
