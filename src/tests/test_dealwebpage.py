from __future__ import annotations

import os
import unittest
from typing import List

from dealwebpage.fix_urls import complete_js_url, remove_query, remove_scheme


class TestCompleteURL(unittest.TestCase):
    def test_remove_query(self):
        url = 'http://www.google.com/url?sa=p&q=http://docs.google.com/comments/d/AAHRpnXvZUGQNsfbGbCOd3qowRdD5b9mvCRlxKsK-2BFkDQ-8tnKBSr1bu9G1k-rJA-tpVdLJlF8KdmpnsArhCkRSO2J51SG_q0py2igYpeYSFp-yNEhv8nf2JBtjg1oYp2Hh0KXr9eny/api/js?anon%3Dtrue%26pref%3D2'
        exp = 'http://www.google.com/url?sa=p&q=http://docs.google.com/comments/d/AAHRpnXvZUGQNsfbGbCOd3qowRdD5b9mvCRlxKsK-2BFkDQ-8tnKBSr1bu9G1k-rJA-tpVdLJlF8KdmpnsArhCkRSO2J51SG_q0py2igYpeYSFp-yNEhv8nf2JBtjg1oYp2Hh0KXr9eny/api/js'
        self.assertEqual(remove_query(url), exp)

        url = 'http://www.google.com/url'
        exp = 'http://www.google.com/url'
        self.assertEqual(remove_query(url), exp)

    def test_remove_scheme(self):
        url = 'http://www.google.com/url1'
        exp = 'www.google.com/url1'
        self.assertEqual(remove_scheme(url), exp)

        url = 'https://www.google.com/url2'
        exp = 'www.google.com/url2'
        self.assertEqual(remove_scheme(url), exp)

        url = 'www.google.com/url3'
        exp = 'www.google.com/url3'
        self.assertEqual(remove_scheme(url), exp)


    def test_complete_js_url(self):
        """
        jsのURLを正しく保管できているか
        dealwebpage/fix_urls.py/complete_js_url()
        """
        src_dir = os.path.dirname(os.path.abspath(__file__))
        html_special_char = []
        with open(src_dir + '/../files/HTML_SPECHAR.txt') as f:
            lines: List[str] = f.read().split('\n')
            for line in lines:
                tuple_line = line.split('\t')
                html_special_char.append(tuple(tuple_line))
                html_special_char.append(('\r', ''))
                html_special_char.append(('\n', ''))

        js_url = complete_js_url(
            'http://www.googletagmanager.com/gtag/js?id=G-MYZTC71T24&amp;l=dataLayer&amp;cx=c',
            'http://www.apu.ac.jp/home/life/',
            html_special_char
        )
        self.assertEqual(js_url, "http://www.googletagmanager.com/gtag/js?id=G-MYZTC71T24&l=dataLayer&cx=c")

        js_url = complete_js_url(
            '//www.youtube.com/iframe_api',
            'http://www.ritsumei.ac.jp/sports-culture/',
            html_special_char
        )
        self.assertEqual(js_url, "http://www.youtube.com/iframe_api")

        js_url = complete_js_url(
            '/script.jsp?id=223327',
            'http://www.ritsumei.ac.jp/top/',
            html_special_char
        )
        self.assertEqual(js_url, "http://www.ritsumei.ac.jp/script.jsp?id=223327")

        js_url = complete_js_url(
            '../js/script.js',
            'http://www.ritsumei.ac.jp/sahs/html/message02/',
            html_special_char
        )
        self.assertEqual(js_url, "http://www.ritsumei.ac.jp/sahs/html/js/script.js")

        js_url = complete_js_url(
            '../../../../js/script.js',
            'http://www.spc.ritsumei.ac.jp/eng/SGH/event_summaries/16event/160704/160704.html',
            html_special_char
        )
        self.assertEqual(js_url, "http://www.spc.ritsumei.ac.jp/eng/js/script.js")

        js_url = complete_js_url(
            'js/self-organization-and-learning-control.20190604135536.js',
            'http://www.rc.is.ritsumei.ac.jp/self-organization-and-learning-control.html',
            html_special_char
        )
        self.assertEqual(js_url, "http://www.rc.is.ritsumei.ac.jp/js/self-organization-and-learning-control.20190604135536.js")


if __name__ == '__main__':
    unittest.main()
