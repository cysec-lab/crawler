import csv
import os
from logging import getLogger
from typing import Any, Dict, List

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from webdrivers.firefox_custom_profile import FirefoxProfile

logger = getLogger(__name__)
this_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = this_dir + '/..'

def make_firefox_options() -> FirefoxOptions:
    # browser settings
    options: FirefoxOptions = FirefoxOptions()
    # headless mode
    options.add_argument('-headless')

    return options


def make_firefox_profile(org_path: str, user_agent: str = '') -> FirefoxProfile:
    """
    args:
        - org_path:     ワークスペースのパス(./)
        - user_agent:   ブラウザのユーザエージェントを設定
    """
    profile: FirefoxProfile = FirefoxProfile()
    profile.accept_untrusted_certs = True

    # User agent
    if user_agent:
        profile.set_preference('general.useragent.override', user_agent)
    # Use addon
    try:
        extention_path = src_dir + '/extensions/CrawlerExtension.xpi'
        profile.add_extension(extension=extention_path)
    except Exception as err:
        logger.exception(f'Failed to add_extension: {err}')

    # Download Manager Settings
    # https://developer.mozilla.org/ja/docs/Download_Manager_preferences

    # set dl file save dir
    if org_path:
        # 0:デスクトップ, 設定がなければデスクトップに保存させる
        # 1:Downloadフォルダ
        # 2:ユーザ定義フォルダ
        profile.set_preference('browser.download.folderList', 2)
        profile.set_preference('browser.download.dir', org_path + '/result/Download')
    else:
        profile.set_preference('browser.download.folderList', 0)
    # DLマネージャーウィンドウを表示しない
    profile.set_preference('browser.download.manager.showWhenStarting', False)
    # 未知の MIME タイプについてどのように開くかを記憶するか
    # http://null.michikusa.jp/config/config_b.html
    profile.set_preference('browser.helperApps.alwaysAsk.force', False)
    # DLマネージャーから実行ファイルを開こうとしたら警告するか
    profile.set_preference('browser.download.manager.alertOnEXEOpen', False)
    # すべてのDLが終わったらDLマネージャーを閉じるか
    profile.set_preference('browser.download.manager.closeWhenDone', True)
    # DLするMIMEタイプ設定
    profile.set_preference('browser.helperApps.neverAsk.saveToDisk', ','.join(make_mimelist()))
    return profile


def make_firefox_caps() -> Dict[str, Any]:
    """
    Firefox Capabilities を設定する、
    """
    # コンソールログを取得するために必要(ffではすべてのログが見れない)
    caps: Dict[str, Any] = DesiredCapabilities.FIREFOX.copy()
    caps['loggingPrefs'] = {
        'browser':      'ALL',
        'driver':       'ALL',
        'client':       'ALL',
        'performance':  'ALL',
        'server':       'ALL'
    }
    caps['acceptInsecureCerts'] = True
    return caps


def make_mimelist() -> List[str]:
    """
    FirefoxでDL可能な MIMEType のリストを作成する
    """
    mime_list: List[str] = list()
    mime_file_dir = src_dir + '/files/mime'
    for csv_file in os.listdir(mime_file_dir):
        if not csv_file.endswith('.csv'):
            continue
        try:
            with open(mime_file_dir + "/" + csv_file) as f:
                csv_reader = csv.DictReader(f)
                for row in csv_reader:
                    if row["Template"]:
                        mime_list.append(row["Template"])
        except csv.Error as err:
            print(f'Faile to make MIME list: {err}')

    return mime_list
