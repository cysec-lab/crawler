import dbm
import time


if __name__ == '__main__':

    d = dbm.open('url', 'n')

    print('make 1000000 data')
    s = time.time()
    for i in range(999997):
        d[str(i)] = 'test'
    d['url1'] = 'ritsu'
    d['url2'] = 'not'
    d['url3'] = 'black'
    print('make time : ' + str(time.time() - s))
    print(len(d))

    print('search')
    s = time.time()
    if 'url1' in d:
        print(d['url1'])
    else:
        print('not found')
    print('search time : ' + str(time.time() - s))

    s = time.time()
    d.close()
    print('close time : ' + str(time.time() - s))

