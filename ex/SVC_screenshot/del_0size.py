# import os


# def del_0size(path, server_list=None):
#     if server_list is None:
#         lis = os.listdir(path)
#     else:
#         lis = server_list.copy()

#     del_dict = dict()
#     for server_name in lis:
#         lis = os.listdir(path + '/' + server_name)
#         img_list = [img_file for img_file in lis if img_file.endswith('.png')]
#         if img_list:
#             for img_file in img_list:
#                 if not os.path.getsize(img_file):
#                     os.remove(img_file)
#                     print('remove file : ' + img_file)
#                     if server_name in del_dict:
#                         del_dict[server_name].append(img_file)
#                     else:
#                         del_dict[server_name] = [img_file]
#         else:
#             os.removedirs(path + '/' + server_name)
#             print('remove dir : ' + server_name)
#     return del_dict


# def rename(path, del_dict):
#     now_dir = os.path.dirname(os.path.abspath(__file__))  # 現在位置を絶対パスで取得
#     os.chdir(path)

#     for server_name, del_list in del_dict.items():
#         os.chdir(server_name)
#         print('next rename : ' + server_name)
#         file_get = os.listdir()
#         sorted_list = sorted([int(i[0:-4]) for i in file_get if i.endswith('.png')], reverse=True)
#         for new_name, del_name in zip(del_list, sorted_list):
#             new_name = new_name[new_name.find('/')+1:]
#             os.rename(str(del_name) + '.png', new_name)
#         os.chdir('..')

#     os.chdir(now_dir)


# def del_0size_and_rename(path):
#     # 画像ファルダpathの中から、ファイルサイズが0のものは削除する
#     re = del_0size(path)
#     if re:
#         rename(path, re)   # 削除すると、連番になっているファイル名が連番じゃなくなるので、調整する


# if __name__ == '__main__':
#     del_0size_and_rename(path='../ROD/screenshots')
