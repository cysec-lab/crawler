import os
import pandas


if __name__ == '__main__':
    path = '../check_result/12/alert'

    kaizan_list = pandas.read_csv(path + '/kaizan_list.csv', header=None)
    if os.path.exists(path + '/kaizan_test.csv'):
        kaizan_test = pandas.read_csv(path + '/kaizan_test.csv', header=None)
    else:
        kaizan_test = pandas.DataFrame()
    if os.path.exists(path + '/appear_iframe_under10_tags_ByMachineLearning.csv'):
        appear_iframe_under10_tags = pandas.read_csv(path + '/appear_iframe_under10_tags_ByMachineLearning.csv', header=None)
    else:
        appear_iframe_under10_tags = pandas.DataFrame()
    if os.path.exists(path + '/iframe_in_server_without_iframe_ByMachineLearning.csv'):
        iframe_in_server_without_iframe = pandas.read_csv(path + '/iframe_in_server_without_iframe_ByMachineLearning.csv', header=None)
    else:
        iframe_in_server_without_iframe = pandas.DataFrame()
    if os.path.exists(path + '/iframe_inspection_ByMachineLearning.csv'):
        iframe_inspection = pandas.read_csv(path + '/iframe_inspection_ByMachineLearning.csv', header=None)
    else:
        iframe_inspection = pandas.DataFrame()
    if os.path.exists(path + '/iframe_in_0_10_ByMachineLearning.csv'):
        iframe_in_0_10 = pandas.read_csv(path + '/iframe_in_0_10_ByMachineLearning.csv', header=None)
    else:
        iframe_in_0_10 = pandas.DataFrame()

    not_found = list()
    for kaizan_url in kaizan_list[0]:
        if not kaizan_test.empty:
            re = kaizan_test[kaizan_test[0].str.contains(kaizan_url)]
            if not re.empty:
                kaizan_test = kaizan_test.drop(re.index.values[0])
                continue

        if not appear_iframe_under10_tags.empty:
            re = appear_iframe_under10_tags[appear_iframe_under10_tags[0].str.contains(kaizan_url)]
            if not re.empty:
                appear_iframe_under10_tags = appear_iframe_under10_tags.drop(re.index.values[0])
                continue

        if not iframe_in_server_without_iframe.empty:
            re = iframe_in_server_without_iframe[iframe_in_server_without_iframe[0].str.contains(kaizan_url)]
            if not re.empty:
                iframe_in_server_without_iframe = iframe_in_server_without_iframe.drop(re.index.values[0])
                continue

        if not iframe_in_0_10.empty:
            re = iframe_in_0_10[iframe_in_0_10[0].str.contains(kaizan_url)]
            if not re.empty:
                iframe_in_0_10 = iframe_in_0_10.drop(re.index.values[0])
                continue

        if not iframe_inspection.empty:
            re = iframe_inspection[iframe_inspection[0].str.contains(kaizan_url)]
            if not re.empty:
                print('found in iframe_inspection')   # continueしてない

        not_found.append(kaizan_url)

    if not appear_iframe_under10_tags.empty:
        appear_iframe_under10_tags.to_csv(path + '/appear_iframe_under10_tags_without_kaizan.csv')
    if not iframe_in_server_without_iframe.empty:
        iframe_in_server_without_iframe.to_csv(path + '/iframe_in_server_without_iframe_without_kaizan.csv')

    print('----NOT FOUND------')
    for i in not_found:
        print(i)
