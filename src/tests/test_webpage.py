from __future__ import annotations

import unittest

from dealwebpage.fix_urls import complete_url_by_html


class TestCompleteURL(unittest.TestCase):
    def test_fix_iframe_url(self):
        iframe_url = "https://www.youtube.com/embed/4PyuD87laW8?loop=1&playlist=4PyuD87laW8&rel=0"
        iframe_html = """
<html dir="ltr" data-cast-api-enabled="true" lang="ja-JP">
<head>
    <script src="/s/player/5dd3f3b2/player_ias"></script>
    <script src="/s/player/5dd3f3b2/player_ias"></script>
    <style>
        html {overflow: hidden;        }body {}
    </style>
    <script src="/s/player/base.js" name="player_ias/base"></script>
    <script src="/yts/fetch-polyfill.js" type="text/javascript" name="fetch-polyfill/fetch-polyfill"></script>
</head>
<body id="" class="date-20210106 ja_JP>
    <div id="player" style="width: 100%; height: 100%;">
    <script src="/s/player/base.js"</script>
</body>
</html>
        """

        exp = """
<html dir="ltr" data-cast-api-enabled="true" lang="ja-JP">
<head>
    <script src="https://www.youtube.com/s/player/5dd3f3b2/player_ias"></script>
    <script src="https://www.youtube.com/s/player/5dd3f3b2/player_ias"></script>
    <style>
        html {overflow: hidden;        }body {}
    </style>
    <script src="https://www.youtube.com/s/player/base.js" name="player_ias/base"></script>
    <script src="https://www.youtube.com/yts/fetch-polyfill.js" type="text/javascript" name="fetch-polyfill/fetch-polyfill"></script>
</head>
<body id="" class="date-20210106 ja_JP>
    <div id="player" style="width: 100%; height: 100%;">
    <script src="https://www.youtube.com/s/player/base.js"</script>
</body>
</html>
        """

        self.assertEqual(complete_url_by_html(iframe_html, iframe_url, list()), exp)



if __name__ == '__main__':
    unittest.main()
