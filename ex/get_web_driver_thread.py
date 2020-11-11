from __future__ import annotations

from logging import getLogger
from multiprocessing import Queue
from os import path
from threading import Thread
from typing import Any, Dict

import selenium.common
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from utils.logger import worker_configurer

from webdrivers.firefox_custom_profile import FirefoxProfile

logger = getLogger(__name__)
geck_path = '/usr/local/bin/geckodriver'
ff_binary = FirefoxBinary('/opt/firefox_dev/firefox')

class GetFirefoxDriverThread(Thread):
    def __init__(self, queue_log: Queue[Any], options: FirefoxOptions, ffprofile: FirefoxProfile, capabilities: Dict[str, Any]):
        super(GetFirefoxDriverThread, self).__init__()
        worker_configurer(queue_log, logger)

        self.options = options
        self.fpro = ffprofile
        self.capabilities = capabilities
        self.driver = False
        self.re = False

    def run(self):
        try:
            logger.debug("get webdriver")
            self.driver = webdriver.Firefox(firefox_binary=ff_binary, executable_path=geck_path, firefox_profile=self.fpro,
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
