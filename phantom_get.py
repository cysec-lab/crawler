from threading import Thread


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
