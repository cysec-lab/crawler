from numpy import array
from random import shuffle
from sklearn.model_selection import train_test_split


def train_data_split(training_data, label_and_identifier, ratio):
    training = list()
    training_label = list()
    test = list()
    test_label = list()
    test_name = list()

    train_ratio = int(len(training_data) * ratio)

    temp_list = [[training_data[i], label_and_identifier[i]] for i in range(len(training_data))]
    shuffle(temp_list)
    for i in range(len(temp_list)):
        if i < train_ratio:
            training.append(temp_list[i][0])
            training_label.append(temp_list[i][1][0])
        else:
            test.append(temp_list[i][0])
            test_label.append(temp_list[i][1][0])
            test_name.append(temp_list[i][1][1])    # どのファイルが間違えたのか見たかったため
    return training, test, training_label, test_label, test_name


# データをトレーニングデータとテストデータに分割
def split_main(training_data, label_identifier, ratio=None):
    data_train, data_test, label_train, label_test = train_test_split(training_data, [l[0] for l in label_identifier])
    file_name_test = list()
    """
    data_train, data_test, label_train, label_test, file_name_test = train_data_split(training_data,
                                                                                      label_identifier, ratio)
    """
    data_train = array(data_train)
    data_test = array(data_test)

    return data_train, data_test, label_train, label_test, file_name_test
