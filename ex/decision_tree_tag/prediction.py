# import pandas as pd


# # テストと結果表示
# def prediction_main(classifier, data_test, label_test, url, src):

#     label_prediction = classifier.predict(data_test)   # 予測

#     # result = {'0->1': 0, '0->2': 0, '1->0': 0, '1->2': 0, '2->0': 0, '2->1': 0}
#     result = pd.DataFrame([[url, src, 0, 0, 0, 0, 0, 0]],
#                           columns=['URL', 'src', '1->0', '2->0', '0->1', '2->1', '0->2', '1->2'])

#     flag = False
#     for i in range(len(label_test)):
#         if label_test[i] != label_prediction[i]:   # 誤分類した場合
#             flag = True
#             result[str(label_test[i])+'->'+str(label_prediction[i])][0] += 1   # 答え -> 予測結果
#     if flag:
#         return result
#     else:
#         return False
