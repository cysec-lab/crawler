import json
import os
import sys

from selenium import webdriver
from typing import Dict, Any

# 以下のページから取ってきた。たしかそのままのはず。。。
# https://a-zumi.net/python-selenium-addon-install/

class FirefoxProfile(webdriver.FirefoxProfile):
    """
    FirefoxProfileの拡張クラス
    """

    def _addon_details(self, addon_path: str) -> Dict[str, Any]:
        """
        install.rdfがない場合、manifest.jsonを探す
        """
        try:
            return super()._addon_details(addon_path) # type: ignore
        except webdriver.firefox.firefox_profile.AddonFormatError:
            try:
                with open(os.path.join(addon_path, 'manifest.json'), 'r', encoding='utf-8_sig') as f:
                    manifest = json.load(f)
                    return {
                        'id': manifest['applications']['gecko']['id'],
                        'version': manifest['version'],
                        'name': manifest['name'],
                        'unpack': False,
                    }
            except (IOError, KeyError) as e:
                raise webdriver.firefox.firefox_profile.AddonFormatError(str(e), sys.exc_info()[2])
