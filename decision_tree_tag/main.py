from glob import glob
import json
from sklearn.tree import DecisionTreeClassifier
from decision_tree_tag import learning, preparation, split


def count_pages(path):
    server_quantity = dict()
    tag_label = dict()
    tag_set = set()
    lis = glob(path + '/*.json')
    for server in lis:
        with open(server, 'r') as f:
            url_dict = json.load(f)
        server_name = server[server.rfind('\\')+1:]
        # URL数をカウント
        server_quantity[server_name] = len(url_dict)
        # tag集合に追加
        for tags_list in url_dict.values():
            for tags in tags_list:
                if tags:
                    tag_set.update(set(tags))
    # tagにラベル付け
    tag_list = list(tag_set)
    i = 0
    for i, tag in enumerate(tag_list):
        if 'iframe' == tag:
            tag_label[tag] = -1
        elif 'invisible_iframe' == tag:
            tag_label[tag] = -2
        else:
            tag_label[tag] = i
    tag_label['NewTag'] = i+1

    return server_quantity, tag_label


def main(path, sample, sample2):
    tree_dict = dict()
    server_without_iframe_set = set()
    cannot_make_vec_server_set = set()

    # 各サーバにどれくらいページがあったかをカウント
    target_server_quantity, tag_label = count_pages(path)
    for target_server, v in sorted(target_server_quantity.items(), key=lambda x: x[1], reverse=True):
        print('next : ' + target_server[0:target_server.find('.')])
        # target_serverのデータ作成
        training_data, label_identifier, kaizan_length = preparation.preparation_main(target_server, path, tag_label,
                                                                                      sample, sample2)
        if training_data is None:   # ページのタグがsample*2個なかったサーバ集合に追加
            cannot_make_vec_server_set.add(target_server[0:target_server.find('.')])
            continue
        elif training_data is False:   # iframeタグが使われていなかったサーバ集合に追加
            server_without_iframe_set.add(target_server[0:target_server.find('.')])
            continue

        # トレーニングデータとテストデータに分ける
        data_train, data_test, label_train, label_test, file_name_test = split.split_main(
            training_data, label_identifier, kaizan_length)

        # モデル作成
        class_ = list()
        if 1 in label_train:
            class_.append(1)
        if 2 in label_train:
            class_.append(2)
        class_weight = {key: 50 for key in class_}   # iframeとinvisible_iframeの重みを50倍にする
        class_weight[0] = 1  # iframe以外のタグの重みは1倍
        best_estimator = DecisionTreeClassifier(criterion='entropy', splitter='best', max_depth=None,
                                                min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0.0,
                                                max_features=None, random_state=None, max_leaf_nodes=None,
                                                presort=False, class_weight=class_weight)
        # 学習
        classifier = learning.learning_main(data_train, label_train, best_estimator)  # 学習
        tree_dict[target_server[0:target_server.find('.')]] = classifier              # 学習器を辞書に登録
        """
        if not os.path.exists('classifier'):
            os.mkdir('classifier')
        joblib.dump(classifier, 'classifier/' + target_server[:target_server.find('.')] + '.tree')
        del classifier
        classifier = tree_dict[target_server[:target_server.find('.')]]

        # 予測と結果表示
        prediction.prediction_main(classifier, data_test, label_test, file_name_test)
        """

    return tree_dict, tag_label, server_without_iframe_set, cannot_make_vec_server_set
