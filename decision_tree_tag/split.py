from numpy import array
from collections import deque


def train_data_split(training_data, label_and_identifier, kaizan_length):
    test = list()
    test_label = list()
    test_name = list()

    # 最後のn個に改ざんデータを入れて、それをテストデータとしている
    temp = deque(training_data.copy())
    temp2 = deque(label_and_identifier.copy())
    for i in range(kaizan_length):
        test.append(temp.pop())
        a = temp2.pop()
        test_label.append(a[0])
        test_name.append(a[1])
    training_data_ = list(temp)
    label_and_identifier_ = list(temp2)
    training = training_data_
    training_label = [i[0] for i in label_and_identifier_]
    return training, test, training_label, test_label, test_name


# データをトレーニングデータとテストデータに分割
def split_main(training_data, label_identifier, kaizan_length):
    data_train, data_test, label_train, label_test, file_name_test = train_data_split(training_data=training_data,
                                                                                      label_and_identifier=label_identifier,
                                                                                      kaizan_length=kaizan_length)
    data_train = array(data_train)
    data_test = array(data_test)
    return data_train, data_test, label_train, label_test, file_name_test
