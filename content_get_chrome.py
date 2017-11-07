from threading import Thread


class DriverGetThread(Thread):
    def __init__(self, options):
        super(DriverGetThread, self).__init__()
        self.options = options
        self.driver = False
        self.re = False

    def run(self):
        from selenium import webdriver
        import selenium.common
        try:
            self.driver = webdriver.Chrome(chrome_options=self.options)
        except selenium.common.exceptions.WebDriverException:
            self.driver = False
        except LookupError:
            self.driver = False
        self.re = True


class PhantomGetThread(Thread):
    def __init__(self, phantom_driver, url):
        super(PhantomGetThread, self).__init__()
        self.phantom_driver = phantom_driver
        self.url = url
        self.re = False

    def run(self):
        try:
            self.phantom_driver.get(self.url)
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
