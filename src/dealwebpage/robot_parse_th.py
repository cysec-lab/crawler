import urllib.error
from logging import Logger
from threading import Thread

from dealwebpage.robotparser import RobotFileParser


class RobotParserThread(Thread):
    """
    Robots.txt にたどり着けなかった場合タイムアウトさせたいので
    robotparser.py をパックしてスレッド化する
    """
    def __init__(self, host: str, logger: Logger):
        super(RobotParserThread, self).__init__()
        self.robots = None
        self.host = host
        self.logger = logger

    def run(self):
        self.logger.debug('creating robots.txt...')
        self.robots = RobotFileParser(url='http://' + self.host + '/robots.txt')
        try:
            self.robots.read()
        except urllib.error.URLError:   # サーバに接続できなければエラーが出る。
            self.robots = None               # robots.txtがなかったら、全てTrueを出すようになる。
        except Exception as err:
            # エラーとして, http.client.RemoteDisconnected などのエラーが出る
            # 'utf-8' codec can't decode byte (http://ritsapu-kr.com/)
            self.logger.exception(f'Exception occur: {err}')
        finally:
            self.logger.debug('creating robots.txt finish')
