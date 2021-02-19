"""
与えたURLのJSをひたすら集めるコード
.csv でJSのファイルを一番はじめのカラムに持つものを与えればいい
使えることを優先したコード...
"""
import logging
import os
import math
import numpy as np
from src.checkers.js_obf import CheckObf, CheckObfResult

DIR_NAME = 'js_files'

logger = logging.getLogger(__name__)

def setLogger():
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s: %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class CheckResults:
    def __init__(self):
        self.read_files = 0
        self.reason_dict = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}
        self.check_result = {CheckObfResult.NORMAL: 0, CheckObfResult.RANDOM: 0, CheckObfResult.ENCODE: 0}
        self.min_alphabets = None
        self.max_alphabets = None
        self.min_numbers = None
        self.max_numbers = None
        self.min_symbols = None
        self.max_symbols = None
        self.min_len = 0
        self.max_len = 0
        self.per_alphabets = []
        self.per_numbers = []
        self.per_symbols = []
        super().__init__()

    def check(self, contents: str):
        check_obf = CheckObf(contents)
        self.check_result[check_obf.check()] += 1
        self.reason_dict[check_obf.reson] += 1
        self.read_files += 1

        self.min_alphabets = min(self.min_alphabets if self.min_alphabets else check_obf.alphabets, check_obf.alphabets)
        self.max_alphabets = max(self.max_alphabets if self.max_alphabets else check_obf.alphabets, check_obf.alphabets)
        self.min_numbers = min(self.min_numbers if self.min_numbers else check_obf.numbers, check_obf.numbers)
        self.max_numbers = max(self.max_numbers if self.max_numbers else check_obf.numbers, check_obf.numbers)
        self.min_symbols = min(self.min_symbols if self.min_symbols else check_obf.symbols, check_obf.symbols)
        self.max_symbols = max(self.max_symbols if self.max_symbols else check_obf.symbols, check_obf.symbols)

        all_chars = check_obf.alphabets + check_obf.numbers + check_obf.symbols

        self.per_alphabets.append(check_obf.alphabets * 100 / all_chars)
        self.per_numbers.append(check_obf.numbers * 100 / all_chars)
        self.per_symbols.append(check_obf.symbols * 100 / all_chars)

def main():
    result = CheckResults()
    if not os.path.exists(DIR_NAME):
        logger.warning('There are no %s dir... Bye.', DIR_NAME)
        return
    for file in os.listdir(DIR_NAME):
        logger.info('FILE_NAME: %s', file)
        with open(DIR_NAME + '/' + file, 'r') as f:
            contents = f.read()
        result.check(contents)

    logger.info('Finish to read %d files!', result.read_files)
    logger.info(result.check_result)
    logger.info(result.reason_dict)
    logger.info('alphabets: %7s %7s', str(result.min_alphabets), str(result.max_alphabets))
    logger.info('numbers  : %7s %7s', str(result.min_numbers), str(result.max_numbers))
    logger.info('symbols  : %7s %7s', str(result.min_symbols), str(result.max_symbols))
    logger.info('alpha_per: %f', math.fsum(result.per_alphabets) / float(result.read_files))
    logger.info('num_per  : %f', math.fsum(result.per_numbers) / float(result.read_files))
    logger.info('sym_per  : %f', math.fsum(result.per_symbols) / float(result.read_files))
    logger.info('alpha_std: %f', np.std(result.per_alphabets))
    logger.info('num_std  : %f', np.std(result.per_numbers))
    logger.info('sym_std  : %f', np.std(result.per_symbols))


if __name__ == "__main__":
    setLogger()
    main()
