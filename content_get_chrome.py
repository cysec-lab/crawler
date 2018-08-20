from threading import Thread


class DriverGetThread(Thread):
    def __init__(self, options, d):
        super(DriverGetThread, self).__init__()
        self.options = options
        self.d = d
        self.driver = False
        self.re = False

    def run(self):
        from selenium import webdriver
        import selenium.common
        try:
            self.driver = webdriver.Chrome(chrome_options=self.options, executable_path='/usr/local/bin/chromedriver',
                                           service_log_path='/home/hiro/Desktop/log.txt', desired_capabilities=self.d)
        except selenium.common.exceptions.WebDriverException as e:
            print(e)
            self.driver = False
        except LookupError as e:
            print(e)
            self.driver = False
        self.re = True


class ChromeGetThread(Thread):
    def __init__(self, chrome_driver, url):
        super(ChromeGetThread, self).__init__()
        self.chrome_driver = chrome_driver
        self.url = url
        self.re = False

    def run(self):
        try:
            self.chrome_driver.get(self.url)
        except Exception as e:
            self.re = e
        else:
            self.re = True


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
