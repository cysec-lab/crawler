from __future__ import annotations

from logging import getLogger
from multiprocessing.queues import Queue
from time import sleep
from typing import Any, Dict, Union, cast

from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from utils.logger import worker_configurer

from webdrivers.firefox_custom_profile import FirefoxProfile
from webdrivers.get_web_driver_thread import GetFirefoxDriverThread
from webdrivers.use_browser import quit_driver
from webdrivers.use_extentions import get_watcher_window
from webdrivers.webdriver_settings import *

logger = getLogger(__name__)

def get_fox_driver(queue_log: Queue[Any], screenshots: bool=False, user_agent: str='', org_path: str='') -> Union[bool, Dict[str, Any]]:
    """
    Firefoxを使うためのdriverをヘッドレスモードで起動
    ファイルダウンロード可能
    RequestURLの取得可能(アドオンを用いて)
    ログコンソールの取得不可能(アドオンの結果は</body>と</html>の間にはさむことで、取得する)
    """
    worker_configurer(queue_log, logger)

    logger.debug("Setting FireFox driver...")
    # headless FireFoxの設定

    options: FirefoxOptions = make_firefox_options()
    profile: FirefoxProfile = make_firefox_profile(org_path, user_agent)
    caps: Dict[str, Any] = make_firefox_caps()

    # Firefoxのドライバを取得。ここでフリーズしていることがあったため、スレッド化した
    # Todo: メモリが足りなかったらドライバーの取得でフリーズする
    try:
        t = GetFirefoxDriverThread(queue_log=queue_log, options=options, ffprofile=profile, capabilities=caps)
        t.start()
        t.join(10.0)
    except Exception as err:
        # runtime error とか
        logger.info(f'Faild to get Firefox Driver Thread, retrying: {err}')
        sleep(10.0)
        pass

    if t.re == False:
        # 1度だけドライバ取得をリトライする
        logger.info('retry to get webdriver')
        if type(t.driver) == WebDriver:
            logger.info('quit past driver')
            driver = cast(WebDriver, t.driver)
            quit_driver(driver) # 一応終了
        try:
            t = GetFirefoxDriverThread(queue_log=queue_log, options=options, ffprofile=profile, capabilities=caps)
            t.start()
            t.join(10.0)
        except Exception as err:
            # runtime error とか
            logger.debug(f'Faild to get Firefox Driver Thread again, Failed: {err}')
            t.re = False
            pass

    if t.re == False:
        # ドライバ取得でフリーズする等のエラー処理
        logger.info("Failed to getting driver: thread freezed")
        if type(t.driver) == WebDriver:
            driver = cast(WebDriver, t.driver)
            quit_driver(driver) # 一応終了させて
        return False
    if t.driver is False:
        # 単にエラーで取得できなかった場合
        logger.info("Failed to getting driver: thread couse error")
        return False

    if type(t.driver) == WebDriver:
        driver = cast(WebDriver, t.driver)
        driver.set_window_size(1280, 1024)
    else:
        return False

    # 拡張機能のwindowIDを取得し、それ以外のwindowを閉じる
    # geckodriver 0.21.0 から HTTP/1.1 になった？ Keep-Aliveの設定が5秒のせいで、5秒間driverにコマンドがいかなかったらPipeが壊れる.
    # 0.20.1 にダウングレードするか、seleniumを最新にアップグレードすると、 Broken Pipe エラーは出なくなる。
    wait = WebDriverWait(driver, 5)
    watcher_window = get_watcher_window(driver, wait)
    if watcher_window is False:
        logger.warning("Fail to get watcher window, return fail")
        quit_driver(driver)
        return False
    watcher_window = cast(Union[str, int], watcher_window)

    logger.debug("Setting FireFox driver... FIN!")
    return {"driver": driver, "wait": wait, "watcher_window": watcher_window}
