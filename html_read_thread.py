from threading import Thread


# urllibでURLを読み込む
class UrlOpenReadThread(Thread):
    def __init__(self, response):
        super(UrlOpenReadThread, self).__init__()
        self.response = response
        self.content = dict()   # HTTPResponseから取得した情報を入れる
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


# ブラウザでURLを読み込む
class WebDriverGetThread(Thread):
    def __init__(self, web_driver, url):
        super(WebDriverGetThread, self).__init__()
        self.web_driver = web_driver
        self.url = url
        self.re = False

    def run(self):
        import time
        try:
            # 回線が悪い時やファイルサイズが大きい時、ここで時間がかかる
            # s = time.time()
            self.web_driver.get(self.url)
            # print("web_driver get time : {}".format(time.time() - s))
        except Exception as e:
            self.re = e
        else:
            self.re = True
