from __future__ import annotations

from logging import getLogger
from os import path
from typing import Any, Dict

import selenium.common
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options as FirefoxOptions
# from utils.logger import worker_configurer

from webdrivers.firefox_custom_profile import FirefoxProfile

logger = getLogger(__name__)
geck_path = '/usr/local/bin/geckodriver'
ff_binary = FirefoxBinary('/opt/firefox_dev/firefox')

class GetFirefoxDriver:
    def __init__(self, options: FirefoxOptions, ffprofile: FirefoxProfile, capabilities: Dict[str, Any]):
        self.options = options
        self.ffprofile = ffprofile
        self.capabilities = capabilities
        self.driver = False
        self.re = False

        try:
            logger.debug("get webdriver")
            self.driver = webdriver.Firefox(firefox_binary=ff_binary, executable_path=geck_path, firefox_profile=self.ffprofile,
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
