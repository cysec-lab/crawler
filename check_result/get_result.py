import os
import pickle


def get_result():
    server_achievement = {}
    os.chdir('D-15/temp')
    print('move to temp/')

    dir_list = os.listdir()
    num = 0
    for dirc in dir_list:
        with open(dirc, 'rb') as f:
            data_temp = pickle.load(f)
            server_achievement[dirc] = data_temp[0]
            num += data_temp[0]

    server_achievement = sorted(server_achievement.items(), key=lambda x: x[1])
    for k, v in server_achievement:
        print(k + ',' + str(v))

    print('total = ' + str(num))


if __name__ == '__main__':
    get_result()
