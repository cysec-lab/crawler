# import pandas as pd


# # テストと結果表示
# def prediction_main(classifier, test_data, url, src, num_diff_word, img_name):
#     label_prediction = classifier.predict(test_data)

#     if label_prediction == 1:  # 1ならば、そのサイトのページとしておかしくない
#         return False
#     # 0だった場合、そのサイトのページではないと判断
#     result = pd.DataFrame([[url, src, num_diff_word, img_name]], columns=['URL', 'src', 'num_diff_word', 'img_file'])

#     return result
