"""
指定したディレクトリ内のjsをjs_obfにかけていろんなデータを取得してCSVに書き出す
"""
import logging
import os
import csv
from js_obf import CheckObf

OUTPUT_FILE = 'result.csv'

DIR_NORMAL = ['data/past_data/normal']
DIR_RANDOM = [
    'data/created_closure_compiler',
    'data/created_yui_compress',
    'data/created_obfscator',
    'data/created_obfscator_compact',
    'data/created_ugilfy'
]
DIR_ENCODE = [
    'data/created_jjencoder',
    'data/created_obfscator_base64',
    'data/created_obfscator_rc4',
    'data/created_obfscator_base64_compact',
    'data/created_obfscator_rc4_compact'
]

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

    for dirs in dir_list:
        for dir in dirs:
            if not os.path.exists(dir):
                logger.warning('There are no %s dir... Bye.', dir)
                return

    for dirs in dir_list:
        for dir in dirs:
            for file in os.listdir(dir):
                logger.info('%s file=%s', dir, file)
                with open(dir + '/' + file, 'r') as f:
                    cobf = CheckObf(f.read())
                    if dirs == DIR_NORMAL:
                        code_type = 0
                    elif dirs == DIR_RANDOM:
                        code_type = 1
                    else:
                        code_type = 2

                    if cobf.src_len != 0:
                        if cobf.len_outwh == 0:
                            alpha_pew = 0
                            num_pew = 0
                            sym_pew = 0
                            blank_pew = 1
                        else:
                            alpha_pew = cobf.alphabets / cobf.len_outwh
                            num_pew = cobf.numbers / cobf.len_outwh
                            sym_pew = cobf.symbols / cobf.len_outwh
                            blank_pew =  cobf.blank / cobf.len_outwh

                        results.append({
                            'type': code_type,
                            'file': file,
                            'dir': dir,
                            'max_len': cobf.max_line,
                            'alphabets': cobf.alphabets,
                            'numbers': cobf.numbers,
                            'symbols': cobf.symbols,
                            'blank': cobf.blank,
                            'unique_chars': cobf.unique_chars,
                            'unique_words': cobf.unique_words,
                            'alpha_per': cobf.alphabets / cobf.src_len,
                            'num_per': cobf.numbers / cobf.src_len,
                            'sym_per': cobf.symbols / cobf.src_len,
                            'blank_per': cobf.blank / cobf.src_len,
                            'alpha_pew': alpha_pew,
                            'num_pew': num_pew,
                            'sym_pew': sym_pew,
                            'blank_pew': blank_pew,
                            'u_chars_per': cobf.unique_chars / cobf.src_len,
                            'u_words_per': cobf.unique_words / cobf.src_len,
                            'u_char>u_word': cobf.unique_chars > cobf.unique_words,
                        })
                    else:
                        logger.info('code_length is 0')
            logger.info('Finish to read %s files!', dir)

    with open(OUTPUT_FILE, 'w') as f:
        writer = csv.DictWriter(f, [
            'type',
            'file',
            'dir',
            'max_len',
            'alphabets',
            'numbers',
            'symbols',
            'blank',
            'unique_chars',
            'unique_words',
            'alpha_per',
            'num_per',
            'sym_per',
            'blank_per',
            'alpha_pew',
            'num_pew',
            'sym_pew',
            'blank_pew',
            'u_chars_per',
            'u_words_per',
            'u_char>u_word'
        ])
        writer.writeheader()
        for result in results:
            writer.writerow(result)


if __name__ == "__main__":
    setLogger()
    main()
