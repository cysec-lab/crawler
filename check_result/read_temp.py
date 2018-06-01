import pickle


if __name__ == '__main__':

    path = '../RAD/temp'

    with open(path + '/progress_www-apu-ac-jp.pickle', 'rb') as f:
        dic = pickle.load(f)

    for key, value in dic.items():
        print(key, value)
