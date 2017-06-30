from sklearn.metrics import confusion_matrix, accuracy_score
import sys
from urllib.parse import urlparse


# テストと結果表示
def prediction_main(classifier, data_test, label_test):

    label_prediction = classifier.predict(data_test)

    result = {'0->1': 0, '0->2': 0, '1->0': 0, '1->2': 0, '2->0': 0, '2->1': 0}
    flag = False
    for i in range(len(label_test)):
        if label_test[i] != label_prediction[i]:   # 誤分類した場合
            flag = True
            result[str(label_test)+'->'+str(label_prediction)] += 1   # 答え -> 予測結果
    if flag:
        return result
    else:
        return False
