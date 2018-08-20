from threading import Thread


class GetFirefoxDriverThread(Thread):
    def __init__(self, options, d, ffprofile):
        super(GetFirefoxDriverThread, self).__init__()
        self.options = options
        self.d = d
        self.fpro = ffprofile
        self.driver = False
        self.re = False

    def run(self):
        from selenium import webdriver
        import selenium.common
        try:
            self.driver = webdriver.Firefox(executable_path='/usr/local/bin/geckodriver', firefox_profile=self.fpro,
                                            log_path='/home/hiro/Desktop/log.txt', desired_capabilities=self.d,
                                            options=self.options)
        except selenium.common.exceptions.WebDriverException as e:
            print(e, flush=True)
            self.driver = False
        except LookupError as e:
            print(e)
            self.driver = False
        self.re = True


class GetChromeDriverThread(Thread):
    def __init__(self, options, d):
        super(GetChromeDriverThread, self).__init__()
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


class GetPhantomJSDriverThread(Thread):
    def __init__(self, des_cap):
        super(GetPhantomJSDriverThread, self).__init__()
        self.des_cap = des_cap
        self.driver = False
        self.re = False

    def run(self):
        from selenium import webdriver
        import selenium.common
        from os import path
        try:
            self.driver = webdriver.PhantomJS(desired_capabilities=self.des_cap, service_log_path=path.devnull,
                                              executable_path='/usr/local/bin/phantomjs')
        except selenium.common.exceptions.WebDriverException:
            self.driver = False
        except LookupError:
            self.driver = False
        self.re = True
