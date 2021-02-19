import unittest
from checkers.html_diff import differ

class TestDiffMethods(unittest.TestCase):
    def test_mod1(self):
        html1 = ['aaa', '111', '121', 'ccc']
        html2 = ['aaa', '111', '222', 'ccc']
        expect = [('modified', ['121'], ['222'])]
        for ans, exp in zip(differ(html1, html2), expect):
            self.assertEqual(ans.data(), exp)

    def test_mod2(self):
        html1 = ['aaa', '111', '121', 'ccc']
        html2 = ['a1a', '111', '222', 'ccc']
        expect = [('modified', ['aaa'], ['a1a']), ('modified', ['121'], ['222'])]
        for ans, exp in zip(differ(html1, html2), expect):
            self.assertEqual(ans.data(), exp)

    def test_del(self):
        html1 = ['aaa', '111', '121', 'ccc']
        html2 = ['aaa', '111', 'ccc']
        expect = [('delete', ['121'], [])]
        for ans, exp in zip(differ(html1, html2), expect):
            self.assertEqual(ans.data(), exp)

    def test_add1(self):
        html1 = ['aaa', '111', 'ccc']
        html2 = ['aaa', '111', '222', 'ccc']
        expect = [('add', ['222'], [])]
        for ans, exp in zip(differ(html1, html2), expect):
            self.assertEqual(ans.data(), exp)

    def test_add2(self):
        html1 = ['aaa', '111', 'ccc']
        html2 = ['bbb', 'aaa', '111', 'ccc']
        expect = [('add', ['bbb'], [])]
        for ans, exp in zip(differ(html1, html2), expect):
            self.assertEqual(ans.data(), exp)

    def test_add3(self):
        html1 = ['aaa', '111', 'ccc']
        html2 = ['aaa', '111', '123', '123', 'ccc']
        expect = [('add', ['123', '123'], [])]
        for ans, exp in zip(differ(html1, html2), expect):
            self.assertEqual(ans.data(), exp)

    def test_mod_add(self):
        html1 = ['aaa', '111', 'ccc']
        html2 = ['aaa', '121', '123', 'ccc']
        expect = [('modified', ['111'], ['121']), ('add', ['123'], [])]
        for ans, exp in zip(differ(html1, html2), expect):
            self.assertEqual(ans.data(), exp)

    def test_mod_add(self):
        html1 = ["""innerIframeSrc":"https://799122680-jotspot-embeds.googleusercontent.com/code/8d87fa64604b2a11fae2ed06104c58d3/inner_iframe.html"},"enableUniversalAnalytics":false,"sharingPolicy":"OPENED","siteTitle":"\u7acb\u547d\u9928\u5927\u5b66 \u60c5\u5831\u7406\u5de5\u5b66\u90e8 \u30b5\u30a4\u30d0\u30fc\u30bb\u30ad\u30e5\u30ea\u30c6\u30a3\u7814\u7a76\u5ba4","jot2atari":{"eligibility":"ineligible"},"onepickUrl":"https://docs.google.com/picker","adsensePublisherId":null,"features":{"moreMobileStyleImprovements":null,"disableGroups":true,"subscriptionDataMigrationInProgress":null,"plusBadge":false},"isPublic":true,"newSitesBaseUrl":"https://sites.google.com","isConsumer":false,"serverFlags":{"jot2AtariLearnMoreUrl":"https://support.google.com/sites/answer/7035197"},"domainAnalyticsAccountId":"","plusPageId":"","signInUrl":"https://accounts.google.com/AccountChooser?continue\u003dhttp://sites.google.com/a/cysec.cs.ritsumei.ac.jp/www/home\u0026service\u003djotspot","analyticsAccountId":"UA-40679231-1","scottyUrl":"/_/upload","homePath":"/","siteNoticeUrlEnabled":null,"plusPageUrl":"","adsensePromoClickedOrSiteIneligible":true,"csiReportUri":"http://csi.gstatic.com/csi","sharingId":"jotspot","termsUrl":"//www.google.com/intl/ja/policies/terms/","gvizVersion":1,"editorResources":{"sitelayout":["http://www.gstatic.com/sites/p/034961/system/app/css/sitelayouteditor.css"],"text":["http://www.gstatic.com/sites/p/034961/system/js/codemirror.js","http://www.gstatic.com/sites/p/034961/system/app/css/codemirror_css.css","http://www.gstatic.com/sites/p/034961/system/js/trog_edit__ja.js","http://www.gstatic.com/sites/p/034961/system/app/css/trogedit.css","/_/rsrc/1606983975000/system/app/css/editor.css","http://www.gstatic.com/sites/p/034961/system/app/css/codeeditor.css","/_/rsrc/1606983975000/system/app/css/camelot/editor-jfk.css"]},"sharingUrlPrefix":"/_/sharing","isAdsenseEnabled":true,"domain":"cysec.cs.ritsumei.ac.jp","baseUri":"","name":"www","siteTemplateId":false,"siteNoticeRevision":null,"siteNoticeUrlAddress":null,"siteNoticeMessage":null,"page":{"isRtlLocale":false,"canDeleteWebspace":null,"isPageDraft":null,"parentPath":null,"parentWuid":null,"siteLocale":"ja","timeZone":"America/Los_Angeles","type":"text","title":"\u30c8\u30c3\u30d7\u30da\u30fc\u30b8","locale":"ja","wuid":"wuid:gx:4c9cb611d6ff6f8d","revision":47,"path":"/home","isSiteRtlLocale":false,"pageInheritsPermissions":null,"name":"home","canChangePath":false,"state":"","properties":{},"bidiEnabled":false,"currentTemplate":{"path":"/system/app/pagetemplates/text","title":"\u30a6\u30a7\u30d6\u30da\u30fc\u30b8"}},"canPublishScriptToAnyone":true,"user":{"keyboardShortcuts":true,"sessionIndex":"","onePickToken":"","guest_":true,"displayNameOrEmail":"guest","userName":"guest","uid":"","renderMobile":false,"domain":"""]
        html2 = ["""innerIframeSrc":"https://939917389-jotspot-embeds.googleusercontent.com/code/8d87fa64604b2a11fae2ed06104c58d3/inner_iframe.html"},"enableUniversalAnalytics":false,"sharingPolicy":"OPENED","siteTitle":"\u7acb\u547d\u9928\u5927\u5b66 \u60c5\u5831\u7406\u5de5\u5b66\u90e8 \u30b5\u30a4\u30d0\u30fc\u30bb\u30ad\u30e5\u30ea\u30c6\u30a3\u7814\u7a76\u5ba4","jot2atari":{"eligibility":"ineligible"},"onepickUrl":"https://docs.google.com/picker","adsensePublisherId":null,"features":{"moreMobileStyleImprovements":null,"disableGroups":true,"subscriptionDataMigrationInProgress":null,"plusBadge":false},"isPublic":true,"newSitesBaseUrl":"https://sites.google.com","isConsumer":false,"serverFlags":{"jot2AtariLearnMoreUrl":"https://support.google.com/sites/answer/7035197"},"domainAnalyticsAccountId":"","plusPageId":"","signInUrl":"https://accounts.google.com/AccountChooser?continue\u003dhttp://sites.google.com/a/cysec.cs.ritsumei.ac.jp/www/home\u0026service\u003djotspot","analyticsAccountId":"UA-40679231-1","scottyUrl":"/_/upload","homePath":"/","siteNoticeUrlEnabled":null,"plusPageUrl":"","adsensePromoClickedOrSiteIneligible":true,"csiReportUri":"http://csi.gstatic.com/csi","sharingId":"jotspot","termsUrl":"//www.google.com/intl/ja/policies/terms/","gvizVersion":1,"editorResources":{"sitelayout":["http://www.gstatic.com/sites/p/034961/system/app/css/sitelayouteditor.css"],"text":["http://www.gstatic.com/sites/p/034961/system/js/codemirror.js","http://www.gstatic.com/sites/p/034961/system/app/css/codemirror_css.css","http://www.gstatic.com/sites/p/034961/system/js/trog_edit__ja.js","http://www.gstatic.com/sites/p/034961/system/app/css/trogedit.css","/_/rsrc/1606983975000/system/app/css/editor.css","http://www.gstatic.com/sites/p/034961/system/app/css/codeeditor.css","/_/rsrc/1606983975000/system/app/css/camelot/editor-jfk.css"]},"sharingUrlPrefix":"/_/sharing","isAdsenseEnabled":true,"domain":"cysec.cs.ritsumei.ac.jp","baseUri":"","name":"www","siteTemplateId":false,"siteNoticeRevision":null,"siteNoticeUrlAddress":null,"siteNoticeMessage":null,"page":{"isRtlLocale":false,"canDeleteWebspace":null,"isPageDraft":null,"parentPath":null,"parentWuid":null,"siteLocale":"ja","timeZone":"America/Los_Angeles","type":"text","title":"\u30c8\u30c3\u30d7\u30da\u30fc\u30b8","locale":"ja","wuid":"wuid:gx:4c9cb611d6ff6f8d","revision":47,"path":"/home","isSiteRtlLocale":false,"pageInheritsPermissions":null,"name":"home","canChangePath":false,"state":"","properties":{},"bidiEnabled":false,"currentTemplate":{"path":"/system/app/pagetemplates/text","title":"\u30a6\u30a7\u30d6\u30da\u30fc\u30b8"}},"canPublishScriptToAnyone":true,"user":{"keyboardShortcuts":true,"sessionIndex":"","onePickToken":"","guest_":true,"displayNameOrEmail":"guest","userName":"guest","uid":"","renderMobile":false,"domain":"""]
        expect = [('modified', ['799122680'], ['939917389'])]
        for ans, exp in zip(differ(html1, html2), expect):
            self.assertEqual(ans.data(), exp)


if __name__ == '__main__':
    unittest.main()