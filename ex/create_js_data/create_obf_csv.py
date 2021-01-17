"""
指定したディレクトリ内のjsをjs_obfにかけていろんなデータを取得してCSVに書き出す
"""
import logging
import os
import csv
from src.checkers.js_obf import CheckObf, CheckObfResult

DIR_NORMAL = 'js_files'
DIR_RANDOM = 'js_files'
DIR_ENCODE = 'js_files'

logger = logging.getLogger(__name__)

def setLogger():
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s: %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def main():
    dir_list = [DIR_NORMAL, DIR_RANDOM, DIR_ENCODE]
    results  = []

    for dir in dir_list:
        if not os.path.exists(dir):
            logger.warning('There are no %s dir... Bye.', dir)
            return

    for dir in dir_list:
        for file in os.listdir(dir):
            logger.info('%s file=%s', dir, file)
            with open(dir + '/' + file, 'r') as f:
                cobf = CheckObf(f.read())
                c = cobf.check()
                if c == CheckObfResult.NORMAL:
                    code_type = 0
                elif c == CheckObfResult.RANDOM:
                    code_type = 1
                else:
                    code_type = 2

                code_length = cobf.alphabets + cobf.numbers + cobf.symbols

                results.append({
                    'type': code_type,
                    'file': file,
                    'max_len': cobf.code_len,
                    'alphabets': cobf.alphabets,
                    'numbers': cobf.numbers,
                    'symbols': cobf.symbols,
                    'unique_chars': cobf.unique_chars,
                    'unique_words': cobf.unique_words,
                    'alpha_per': cobf.alphabets / code_length,
                    'num_per': cobf.numbers / code_length,
                    'sym_per': cobf.symbols / code_length,
                    'u_chars_per': cobf.unique_chars / code_length,
                    'u_words_per': cobf.unique_words / code_length,
                })
        logger.info('Finish to read %s files!', dir)

    with open('result.csv', 'w') as f:
        writer = csv.DictWriter(f, [
            'type',
            'file',
            'max_len',
            'alphabets',
            'numbers',
            'symbols',
            'unique_chars',
            'unique_words',
            'alpha_per',
            'num_per',
            'sym_per',
            'u_chars_per',
            'u_words_per'
        ])
        writer.writeheader()
        for result in results:
            writer.writerow(result)


if __name__ == "__main__":
    setLogger()
    main()
