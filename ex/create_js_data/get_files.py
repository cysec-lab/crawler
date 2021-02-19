"""
与えたURLのJSをひたすら集めるコード
.csv でJSのファイルを一番はじめのカラムに持つものを与えればいい
使えることを優先したコード...
"""
import logging
import os
from hashlib import sha256
from time import sleep
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen

FILE_NAME = 'js_list.txt'
DIR_NAME  = 'js_files'

logger = logging.getLogger(__name__)

class DistinctError(ValueError):
    """distinctditc's error type"""

class Distinctdict(dict):
    """dict extended class"""
    def __setitem__(self, key: str, value: Any) -> None:
        if value in self.values():
            if (
                (key in self and self[key] != value) or
                key not in self
            ):
                raise DistinctError(
                    "This value already exists in DistinctDict"
                )
        super().__setitem__(key, value)

def setLogger():
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s: %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def main():
    file_dict = Distinctdict()
    if not os.path.exists(FILE_NAME):
        logger.info('There are no input file... Bye...')
        return
    
    with open(FILE_NAME, 'r') as f:
        file = f.readlines()
    
    if not os.path.exists(DIR_NAME):
        os.mkdir(DIR_NAME)

    for line in file[1:]:
        url = line.split(',')[0].replace('\n', '')
        logger.info('target_url: %s', url)

        try:
            page = urlopen(url=url, timeout=5)
        except UnicodeEncodeError as err:
            logger.warning(f'{err}')
            continue
        except Exception as err:
            logger.exception(f'{err}')
            continue

        logger.info('open url  : %s', url)
        file_name = make_file_name(url)
        logger.info('save to   : %s', file_name)
        js_src = page.read()
        
        try:
            file_dict[file_name] = sha256(js_src).hexdigest()
            with open(DIR_NAME + '/' + file_name, 'w') as f:
                f.write(js_src.decode())
            logger.info('saved!    : %s', file_name)
        except DistinctError as message:
            logger.info(f'{message}')
            pass
        except Exception as err:
            logger.exception(f'{err}')
        sleep(1)
    logger.info('Finish save %d files!', len(file_dict))


def make_file_name(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.replace('/', '-') if parsed.path else ""
    return parsed.netloc + path


if __name__ == "__main__":
    setLogger()
    main()
