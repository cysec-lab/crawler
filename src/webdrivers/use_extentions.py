from __future__ import annotations

from logging import getLogger
from typing import Any, Union

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from webpage import Page

logger = getLogger(__name__)


def get_watcher_window(driver: WebDriver, wait: WebDriverWait) -> Union[bool, int, str]:
    """
    driverを取得した直後に呼ぶ
    Watcherタブ以外を消してWatcherタブを開く
    """
    watcher_window = False
    logger.debug("Try to access extension page")
    try:
        wait.until(expected_conditions.visibility_of_all_elements_located((By.ID, "button")))
        wait.until(expected_conditions.presence_of_element_located((By.ID, "DoneAttachJS")))
    except TimeoutException as err:
        print(f"failed to access extension page by timeout: {err}")
        return False
    except Exception as err:
        print(f'failed to access extension page: {err}')
        return False

    try:
        windows: list[Union[int, str]] = driver.window_handles
        for window in windows:
            driver.switch_to.window(window)
            title = driver.title
            if title == "Watcher":
                watcher_window = window
            else:
                # 不要なページを消す
                driver.close()
    except Exception as err:
        # 最悪、エラーが起きてもwatcher_windowがわかればよい
        pass

    try:
        driver.switch_to.window(watcher_window)
    except Exception as err:
        logger.exception(f"Faild to switch extension page: {err}")
        return False
    else:
        return watcher_window

def stop_watcher_and_get_data(driver: WebDriver, wait: WebDriverWait, watcher_window: Union[str, int], page: Page) -> bool:
    """
    Watcher.htmlのStop Watchingボタンをクリック。
    拡張機能が監視を終え、収集したデータを記録。
    """
    logger.debug("Watcher: stop")
    try:
        # watcher.htmlに移動してstopをクリック
        # クリックすると、Watcher.htmlのdivタグ(id="contents")の中に、収集したデータを記録する
        driver.switch_to.window(watcher_window)
        wait.until(expected_conditions.visibility_of_element_located((By.ID, "stop")))
        elm = driver.find_element_by_id("stop")
        elm.click()

        # contentsの最後の要素がDOMに現れるまで待つ
        wait.until(expected_conditions.presence_of_element_located((By.ID, "EndOfData")))

        # watcher.htmlのHTMLをpageインスタンスのプロパティに保存
        page.watcher_html = driver.page_source # type: ignore

        # clearContentsをクリック
        elm: Any = driver.find_element_by_id("clearContents")
        elm.click()
        # 最後の要素が消えるまで待つ
        wait.until(expected_conditions.invisibility_of_element_located((By.ID, "EndOfData")))
    except Exception as err:
        logger.exception(f'{err}')
        return False
    else:
        logger.debug("Watcher: Get data from Watcher")
        return True


def start_watcher_and_move_blank(driver: WebDriver, wait: WebDriverWait, watcher_window: Union[int, str], blank_window: str) -> bool:
    """
    watcher.htmlのStart Watchingボタンをクリック。拡張機能が監視を始める
    """
    logger.debug("Watcher: starting...")
    try:
        driver.switch_to.window(watcher_window)
        wait.until(expected_conditions.visibility_of_element_located((By.ID, "start")))
        elm: Any = driver.find_element_by_id("start")
        elm.click()
        driver.switch_to.window(blank_window)
        wait.until(lambda d: "Watcher" != driver.title) # type: ignore
    except Exception as err:
        logger.exception(f'{err}')
        return False
    else:
        return True
