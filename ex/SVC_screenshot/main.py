import time
import os
import sys
import numpy
from sklearn.svm import LinearSVC
from sklearn.model_selection import GridSearchCV
from sklearn.feature_selection import SelectKBest
from sklearn.multiclass import OneVsRestClassifier, OneVsOneClassifier
from sklearn.externals import joblib
from sklearn import decomposition
from SVC_screenshot.preparation import preparation_main
from SVC_screenshot.learning import learning_main
from SVC_screenshot.split import split_main
from SVC_screenshot.prediction import prediction_main


def grid_search(d, l, svm):
    # C:高いとはずれ値を許容しない gamma:高いと複雑な分類線を引く
    parameters = {'C': numpy.logspace(-5, 15, 21, base=2)}
    clf = GridSearchCV(svm, parameters, cv=5, n_jobs=-1)
    clf.fit(d, l)
    return clf.best_estimator_


def count_pages(path):
    target_server_quantity = dict()
    lis = os.listdir(path)
    for target_server in lis:
        if os.path.isdir(path + '/' + target_server):
            target_server_quantity[target_server] = len(os.listdir(path + '/' + target_server))
    return target_server_quantity


def main(path):
    svc_dict = dict()
    MAX = 200    # データが多いとメモリ足んなくて終わらないので上限

    # 各サーバにどれくらいページがあったかをカウント
    target_server_quantity = count_pages(path)
    for target_server, v in sorted(target_server_quantity.items(), key=lambda x: x[1], reverse=True):

        print('-------- next : ' + target_server + ' quantity: ' + str(min(target_server_quantity[target_server], MAX)))

        # target_serverとそれ以外で分類するために,同じ量の正誤データを準備する
        training_data, label_identifier = preparation_main(target_server, target_server_quantity, MAX, path)

        # 主成分分析で次元削減
        """
        """
        print('dimension = ' + str(len(training_data[0])))
        pca = decomposition.PCA()
        s = time.time()
        training_data = pca.fit_transform(training_data)
        print('decreased dimension = ' + str(len(training_data[0])))
        print('PCA time = ' + str(time.time() - s))

        # グリッドサーチで評価の高いモデル作成
        """
        print('grid search...')
        s = time.time()
        best_estimator = grid_search(training_data, [label[0] for label in label_identifier], LinearSVC())
        print('grid search time = ' + str(time.time() - s))
        print(best_estimator)
        """
        best_estimator = LinearSVC(C=0.03125)
        # classifier = OneVsOneClassifier(best_estimator, n_jobs=-1)

        # 学習
        # classifier = learning_main(training_data, [l[0] for l in label_identifier], best_estimator)
        # svc_dict[target_server] = classifier

        data_train, data_test, label_train, label_test, file_name_test = split_main(training_data, label_identifier)
        classifier = learning_main(data_train, label_train, best_estimator)
        # 予測
        from sklearn.metrics import confusion_matrix, accuracy_score
        predict_labels = classifier.predict(data_test)
        test_result = confusion_matrix(label_test, predict_labels)
        for i in test_result:
            print(i)
        print('score :', accuracy_score(label_test, predict_labels))
        break

    return svc_dict

if __name__ == '__main__':
    start = time.time()
    main(path='../ROD/screenshots')
    print('run time = ' + str(time.time() - start))
