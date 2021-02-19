from __future__ import annotations

import unittest
from multiprocessing import Queue
from typing import Any, Dict, Union, cast

from webdrivers.use_browser import set_html
from webdrivers.webdriver_init import get_fox_driver
from dealwebpage.webpage import Page


class TestStringMethods(unittest.TestCase):
    def test_get_fox_driver(self):
        """
        webdriverにアクセスできるかの確認
        """
        queue_log: Queue[Any] = Queue()
        driver_info = get_fox_driver(queue_log, org_path='/dev/null')
        self.assertIsNot(driver_info, False)
        driver_info["driver"].quit() # type: ignore

    def test_get_html_by_foxdriver(self):
        """
        Webdriverを用いて実際にHPが取得できているかを確認
        """
        page: Page = Page("http://abehiroshi.la.coocan.jp/", "", [])
        queue_log: Queue[Any] = Queue()
        driver_info: Union[bool, Dict[str, Any]] = get_fox_driver(queue_log, org_path='/dev/null')
        self.assertIsNot(driver_info, False)
        driver_info = cast(Dict[str, str], driver_info)
        driver = driver_info["driver"]
        _ =set_html(page, driver)
        expect = """<html><head>
<meta http-equiv="Content-Type" content="text/html; charset=Shift_JIS">
<meta name="GENERATOR" content="JustSystems Homepage Builder Version 20.0.6.0 for Windows">
<meta http-equiv="Content-Style-Type" content="text/css">
<title>阿部寛のホームページ</title>
</head>
<frameset cols="18,82">
  <frame src="menu.htm" marginheight="0" marginwidth="0" scrolling="auto" name="left">
  <frame src="top.htm" marginheight="0" marginwidth="0" scrolling="auto" name="right">
  <noframes>
  <body></body>
  </noframes>
</frameset>
</html>"""
        self.assertEqual(page.html, expect)
        driver.quit()

    def test_get_malformed_html(self):
        """
        存在しないURLで失敗することの確認
        """
        page: Page = Page("hogehoge", "", [])
        queue_log: Queue[Any] = Queue()
        driver_info: Union[bool, Dict[str, Any]] = get_fox_driver(queue_log, org_path='/dev/null')
        self.assertIsNot(driver_info, False)
        driver_info = cast(Dict[str, str], driver_info)
        driver = driver_info["driver"]
        i =set_html(page, driver)
        print(i)
        print(page.html)
        self.assertEqual(i[0], "Error_WebDriver")
        driver.quit()


if __name__ == '__main__':
    unittest.main()
