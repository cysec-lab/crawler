from __future__ import annotations

from logging import getLogger
from multiprocessing import Queue
from os import path
from threading import Thread
from typing import Any

import selenium.common
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from FirefoxProfile_new import FirefoxProfile
from location import location
from logger import worker_configurer

logger = getLogger()

class GetFirefoxDriverThread(Thread):
    def __init__(self, queue_log: Queue[Any], options: FirefoxOptions, ffprofile: FirefoxProfile):
        super(GetFirefoxDriverThread, self).__init__()
        worker_configurer(queue_log, logger)
        logger.debug("initial get firefox driver thread")

        self.options = options
        self.fpro = ffprofile
        self.driver = False
        self.re = False

    def run(self):
        try:
            logger.debug("get webdriver")
            self.driver = webdriver.Firefox(executable_path='/usr/local/bin/geckodriver', firefox_profile=self.fpro,
                                            options=self.options, log_path=path.devnull)
        except selenium.common.exceptions.WebDriverException as e:
            logger.error(f'Web Driver exception: {e}')
            self.driver = False
        except LookupError as e:
            logger.error(f'Look up error: {e}')
            self.driver = False
        except Exception as err:
            logger.exception(f'{err}')
            self.driver = False
        finally:
            self.re = True


# class GetChromeDriverThread(Thread):
#     def __init__(self, options, d):
#         super(GetChromeDriverThread, self).__init__()
#         self.options = options
#         self.d = d
#         self.driver = False
#         self.re = False

#     def run(self):
#         try:
#             self.driver = webdriver.Chrome(chrome_options=self.options, executable_path='/usr/local/bin/chromedriver',
#                                            desired_capabilities=self.d)
#         except selenium.common.exceptions.WebDriverException as e:
#             print(location() + str(e), flush=True)
#             self.driver = False
#         except LookupError as e:
#             print(location() + str(e), flush=True)
#             self.driver = False
#         finally:
#             self.re = True
