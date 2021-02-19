from __future__ import annotations

import unittest
from multiprocessing import Queue
from typing import Any, Dict, Union, cast

from webdrivers.use_extentions import get_watcher_window
from webdrivers.webdriver_init import get_fox_driver


class TestStringMethods(unittest.TestCase):
    def test_get_watcher_page(self):
        """
        Watcher Pageを取得できているかの確認
        """
        from selenium.webdriver.remote.webelement import WebElement
        from selenium.webdriver.support.ui import WebDriverWait

        queue_log: Queue[Any] = Queue()
        driver_info: Union[bool, Dict[str, Any]] = get_fox_driver(queue_log, org_path='/dev/null')
        self.assertIsNot(driver_info, False)
        driver_info = cast(Dict[str, str], driver_info)
        driver = driver_info["driver"]
        wait: WebDriverWait = WebDriverWait(driver, 5)
        id = get_watcher_window(driver, wait)
        driver.switch_to.window(id)
        home: WebElement = driver.find_element_by_id("home")
        self.assertEqual(home.text, "Watcher Home Page") # type: ignore
        driver.quit()

if __name__ == '__main__':
    unittest.main()
