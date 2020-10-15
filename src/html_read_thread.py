from threading import Thread
from typing import Any, Dict, Union

from selenium.webdriver.firefox.webdriver import WebDriver

class UrlOpenReadThread(Thread):
    """
    urllibでURLを読み込む
    """
    def __init__(self, response: Any):
        super(UrlOpenReadThread, self).__init__()
        self.response = response
        self.content: Dict[str, Any] = dict()   # HTTPResponseから取得した情報を入れる
        self.re = False

    def run(self):
        try:
            self.content['encoding'] = self.response.info().get_content_charset(failobj='utf-8')
            self.content['html_urlopen'] = self.response.read()
            self.content['url_urlopen'] = self.response.geturl()
            self.content['content_type'] = self.response.getheader('Content-Type')
            self.content['content_length'] = self.response.getheader('Content-Length')
        except Exception as e:
            self.re = e
        else:
            self.re = True


class WebDriverGetThread(Thread):
    """
    ブラウザでURLを読み込む
    """
    def __init__(self, web_driver: WebDriver, url: str):
        super(WebDriverGetThread, self).__init__()
        self.web_driver = web_driver
        self.url: str = url
        self.re: Union[bool, Exception] = False

    def run(self):
        try:
            # 回線が悪い時やファイルサイズが大きい時、ここで時間がかかる
            # s = time.time()
            self.web_driver.get(self.url) # type: ignore
            # print("web_driver get time : {}".format(time.time() - s))
        except Exception as e:
            self.re = e
        else:
            self.re = True
