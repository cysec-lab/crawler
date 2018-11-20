import os
import cv2
import random
import numpy
import time


def get_array_from_tb(img):
    height, width = img.shape[0:2]
    height_resize = int(height / 6)
    width_resize = int(width / 4)

    tb_size = (200, 300)  # width * height
    lr_size = (33, 66)  # width * height
    img_top = img[0:height_resize, 0:width]
    inter = cv2.INTER_LINEAR
    img_top = cv2.resize(img_top, tb_size, interpolation=inter)
    img_bottom = img[height - height_resize:height, 0:width]
    img_bottom = cv2.resize(img_bottom, tb_size, interpolation=inter)
    img_left = img[height_resize:height - height_resize, 0:width_resize]
    img_left = cv2.resize(img_left, lr_size, interpolation=inter)
    img_right = img[height_resize:height - height_resize, width - width_resize:width]
    img_right = cv2.resize(img_right, lr_size, interpolation=inter)

    array = numpy.append(img_top, img_bottom)
    array = numpy.append(array, img_left)
    array = numpy.append(array, img_right)
    return array


def get_array_from_feature(img):
    detector = cv2.ORB_create()
    keypoints = detector.detect(img)
    if len(keypoints) < 200:
        i = 0
        if len(keypoints) == 0:
            return False
        else:
            while len(keypoints) < 200:
                keypoints += keypoints
        """
        detectors = [cv2.FastFeatureDetector_create(), cv2.AgastFeatureDetector_create(), cv2.MSER_create(),
                     cv2.AKAZE_create(), cv2.BRISK_create(), cv2.SimpleBlobDetector_create()]
        while len(keypoints) < 200:
            detector = detectors[i]
            keypoints += detector.detect(img)
            i += 1
            if i == len(detectors):
                while len(keypoints) < 200:
                    keypoints += keypoints
                break
        """
    keypoints = keypoints[0:100] + keypoints[len(keypoints) - 100:]
    array = list()
    z = 5
    for i in keypoints:
        x, y = i.pt
        y = int(x)
        x = int(y)
        temp = img[x - z: x + z, y - z:y + z]
        array = numpy.append(array, temp)
    return array


def get_matrix_from_img(filename):
    img = cv2.imread(filename)
    if img is None:
        array = False
        print('load failed : ' + filename)    # サイズ0の場合など。サイズ0の画像は消すため多分ない。
    else:
        img_array = cv2.resize(img, (600, 600))
        return img_array.reshape(1, img_array.shape[0] * img_array.shape[1] * img_array.shape[2])[0]
        # array = get_array_from_tb(img)
    return array


def make_training_data(server_dict, target_server, path):
    training_data = list()
    label_identifier = list()

    for server, quantity in server_dict.items():
        lis = os.listdir(path + '/' + server)
        random.shuffle(lis)
        if server == target_server:
            label = 1
        else:
            label = 0
        for i, file_name in enumerate(lis):
            if i == quantity:
                break
            if file_name.endswith('.png'):
                img_vec = get_matrix_from_img(path + '/' + server + '/' + file_name)    # 加工画像のベクトル取得
                if img_vec is False:
                    continue
                training_data.append(img_vec)
                label_identifier.append([label, file_name])
    return training_data, label_identifier


def equal(target_server, server_quantity, MAX):
    searching_num = min(server_quantity[target_server], MAX)
    # 別のフォルダから
    another_quantity_dict = dict()
    target_list = list(server_quantity.keys())
    target_list.remove(target_server)
    while searching_num:
        i = random.choice(target_list)
        if i in another_quantity_dict:
            if another_quantity_dict[i] < server_quantity[i]:
                another_quantity_dict[i] += 1
                searching_num -= 1
            else:
                target_list.remove(i)
        else:
            another_quantity_dict[i] = 1
            searching_num -= 1
        if not target_list:
            break
    return another_quantity_dict


def preparation_main(target_server, server_quantity, MAX, path):
    # serverと同じ量の誤りデータを準備する
    server_dict = equal(target_server, server_quantity, MAX)
    print('pick up data from ' + str(server_dict.items()))

    # serverのデータ作成
    server_dict[target_server] = min(server_quantity[target_server], MAX)
    s = time.time()
    training_data, label_identifier = make_training_data(server_dict, target_server, path)
    print('preparation time = ' + str(time.time() - s))

    return training_data, label_identifier
