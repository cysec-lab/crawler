from threading import Thread
from selenium import webdriver
import selenium.common
from os import path


class DriverGetThread(Thread):
    def __init__(self, des_cap):
        super(DriverGetThread, self).__init__()
        self.des_cap = des_cap
        self.driver = False
        self.re = False

    def run(self):
        try:
            self.driver = webdriver.PhantomJS(desired_capabilities=self.des_cap, service_log_path=path.devnull)
        except selenium.common.exceptions.WebDriverException:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = False
        except LookupError:
            try:
                self.driver.quit()
            except Exception:
                pass
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
