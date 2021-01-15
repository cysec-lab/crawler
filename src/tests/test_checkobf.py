from __future__ import annotations

import unittest

from checkers.js_obf import CheckObf, CheckObfResult

class TestCompleteURL(unittest.TestCase):
    def test_check_obf_functions(self):
        src = """
function make_link(){
    var link3 = document.createElement("a");
    document.body.appendChild(link3);
    link3.id = "download";
    link3.href = "#";
    link3.download = "restart.bat";
}
function click_dl(){
    var link3 = document.getElementById("download");
    link3.click();
    document.body.removeChild(link3);
}
"""
        check_obf = CheckObf(src)
        self.assertEqual(check_obf.check(), CheckObfResult.NORMAL)
        self.assertEqual(check_obf.check_chars_of_line(), 52)
        self.assertEqual(check_obf.check_total_unique_chars(), 8)
        self.assertEqual(check_obf.check_total_unique_words(), 0)

    def test_check_obf(self):
        # リダイレクトでべつのサイトに飛ばされる系JS(多少消している)
        src = """
var _hmt = _hmt || [];
(function() {
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com";
  var s = document.getElementsByTagName("script")[0]; 
  s.parentNode.insertBefore(hm, s);
})();

$=~[];$={___:++$,$$$$:(![]+"")[$][]+"")[$],_$_:++$,$_$$:({}+"")[$],$$_$:($[$]+"")[$],_$$:++$,$$$_:(!""+"")[$],$__:++$,$_$:++$,$$__:({}+"")[$],$$_:++$,$$$:++$,$___:++$,$__$:++$};$.$_=($.$_=$+"")[$.$_$]+($._$=$.$_[$.__$])+($.$$=($.$+"")$.$_[$.$_$]+$.__+$._$+$.$;$.$$=$.$+(!""+"")[$._$$]+$.__+$._+$.$+$.$$;$.$=($.___)[$.$_][$.$_];$.$($.$($.$$+"\""+$.$$_$+$._$+$.$$__+$._+"\\"+$.__$+$.$_$+$.$_$+$.$$$_+"\\"+$.__$+$.$_$+$.$$_+$.__+".\\"+$.__$+$.$$_+$.$$$+"\\"+$.__$+$.$$_+$._$_+"\\"+$.__$+$.$_$+$.__$+$.__+$.$$$_+(![]+"")[$._$_]+"\\"+$.__$+$.$_$+$.$$_+"(\\\"<"+$.$_$$+"\\"+$.__$+$.$$_+$._$_+"><"+$.$$__+$.$$$_+"\\"+$.__$+$.$_$+$.$$_+$.__+$.$$$_+"\\"+$.__$+$.$$_+$._$_+"><\\"+$.__$+$.$$_+$.___+"\\"+$.$__+$.___+"\\"+$.__$+$.$$_+$._$$+$.__+"\\"+$.__$+$.$$$+$.__$+(![]+"")[$._$_]+$.$$$_+"=\\\\'"+$.$$$$+$._$+"\\"+$.__$+$.$_$+$.$$_+$.__+"-\\"+$.__$+$.$$_+$._$$+"\\"+$.__$+$.$_$+$.__$+"\\"+$.__$+$.$$$+$._$_+$.$$$_+":"+$._$_+$._$$+"\\"+$.__$+$.$$_+$.___+"\\"+$.__$+$.$$$+$.___+";\\\\'>\\"+$._+$.$$$+$.$$$$+$.$_$+$.__$+"\\"+$._+$.$$$+$.$_$_+$.$$_$+$.$__$+"\\"+$._+$.$$_+$.$_$$+$.$$_+$._$$+"\\"+$._+$.$_$+$.$$$+$._$_+$.$___+"\\"+$._+$.$_$+$._$_+$.$_$_+$.___+"\\"+$._+$.$___+$.$$$$+$.$$$+$.$$_$+"\\"+$._+$.$__+$.$$$_+$._$_+$.$$_$+"\\"+$.$__+$.___+".\\"+$.$__+$.___+".\\"+$.$__+$.___+".\\"+$.$__+$.___+"\\"+$._+$.$___+$.$_$$+$.$$$$+$.$$$+"\\"+$._+$.$$$+$.$_$_+$.___+$.$$_$+"\\"+$._+$.$_$+$.$__+$.___+$.$$$_+"\\"+$.$__+$.___+".\\"+$.$__+$.___+".\\"+$.$__+$.___+".\\"+$.$__+$.___+".\\"+$.$__+$.___+"</\\"+$.__$+$.$$_+$.___+"></"+$.$$__+$.$$$_+"\\"+$.__$+$.$_$+$.$$_+$.__+$.$$$_+"\\"+$.__$+$.$$_+$._$_+">\\\");\\"+$.__$+$._$_+"\\"+$.__$+$.$$_+$.$$_+$.$_$_+"\\"+$.__$+$.$$_+$._$_+"\\"+$.$__+$.___+$.$_$_+"\\"+$.$__+$.___+"=\\"+$.$__+$.___+"\\"+$.__$+$.$_$+$.$$_+$.$$$_+"\\"+$.__$+$.$$_+$.$$$+"\\"+$.$__+$.___+"\\"+$.__$+$.___+$.__$+"\\"+$.__$+$.$$_+$._$_+"\\"+$.__$+$.$$_+$._$_+$.$_$_+"\\"+$.__$+$.$$$+$.__$+"();\\"+$.__$+$._$_+$.$_$_+"["+$.___+"]\\"+$.$__+$.___+"=\\"+$.$__+$.___+"\\\"\\"+$.__$+$.$_$+$.___+$.__+$.__+"\\"+$.__$+$.$$_+$.___+"\\"+$.__$+$.$$_+$._$$+"://\\"+$.__$+$.$$_+$.__$+"\\"+$.__$+$.$__+$.$$$+$.$$__+$._$$+$.$_$+$._$$+"."+$.$$__+$._$+"\\"+$.__$+$.$_$+$.$_$+"/\\"+$.__$+$.$$_+$._$_+$.$$$_+"\\"+$.__$+$.$__+$.$$$+"\\"+$.__$+$.$_$+$.__$+"\\"+$.__$+$.$$_+$._$$+$.__+$.$$$_+"\\"+$.__$+$.$$_+$._$_+"?\\"+$.__$+$.$_$+$.__$+$.$$_$+"="+$.$__$+$._$$+$.___+$.___+$.$$$+$.$$$+$.__$+$.$_$+"\\\";\\"+$.__$+$._$_+$.$_$_+"["+$.__$+"]\\"+$.$__+$.___+"=\\"+$.$__+$.___+"\\\"\\"+$.__$+$.$_$+$.___+$.__+$.__+"\\"+$.__$+$.$$_+$.___+"\\"+$.__$+$.$$_+$._$$+"://\\"+$.__$+$.$$_+$.__$+"\\"+$.__$+$.$__+$.$$$+$.$$__+$._$$+$.$_$+$._$$+"."+$.$$__+$._$+"\\"+$.__$+$.$_$+$.$_$+"/\\"+$.__$+$.$$_+$._$_+$.$$$_+"\\"+$.__$+$.$__+$.$$$+"\\"+$.__$+$.$_$+$.__$+"\\"+$.__$+$.$$_+$._$$+$.__+$.$$$_+"\\"+$.__$+$.$$_+$._$_+"?\\"+$.__$+$.$_$+$.__$+$.$$_$+"="+$.$__$+$._$$+$.___+$.___+$.$$$+$.$$$+$.__$+$.$_$+"\\\";\\"+$.__$+$._$_+$.$_$_+"["+$._$_+"]\\"+$.$__+$.___+"=\\"+$.$__+$.___+"\\\"\\"+$.__$+$.$_$+$.___+$.__+$.__+"\\"+$.__$+$.$$_+$.___+"\\"+$.__$+$.$$_+$._$$+"://\\"+$.__$+$.$$_+$.__$+"\\"+$.__$+$.$__+$.$$$+$.$$__+$._$$+$.$__$+$._$$+"."+$.$$__+$._$+"\\"+$.__$+$.$_$+$.$_$+"/\\"+$.__$+$.$$_+$._$_+$.$$$_+"\\"+$.__$+$.$__+$.$$$+"\\"+$.__$+$.$_$+$.__$+"\\"+$.__$+$.$$_+$._$$+$.__+$.$$$_+"\\"+$.__$+$.$$_+$._$_+"?\\"+$.__$+$.$_$+$.__$+$.$$_$+"="+$.$__$+$._$$+$.___+$.___+$.$$$+$.$$$+$.__$+$.$_$+"\\\";\\"+$.__$+$._$_+"\\"+$.__$+$.$_$+$.$_$+"\\"+$.$__+$.___+"=\\"+$.$__+$.___+"\\"+$.__$+$.__$+$.$_$+$.$_$_+$.__+"\\"+$.__$+$.$_$+$.___+"."+$.$$$$+(![]+"")[$._$_]+$._$+$._$+"\\"+$.__$+$.$$_+$._$_+"(\\"+$.__$+$.__$+$.$_$+$.$_$_+$.__+"\\"+$.__$+$.$_$+$.___+".\\"+$.__$+$.$$_+$._$_+$.$_$_+"\\"+$.__$+$.$_$+$.$$_+$.$$_$+$._$+"\\"+$.__$+$.$_$+$.$_$+"()\\"+$.$__+$.___+"*\\"+$.$__+$.___+$._$$+");\\"+$.__$+$._$_+(![]+"")[$._$_]+$._$+$.$$__+$.$_$_+$.__+"\\"+$.__$+$.$_$+$.__$+$._$+"\\"+$.__$+$.$_$+$.$$_+".\\"+$.__$+$.$_$+$.___+"\\"+$.__$+$.$$_+$._$_+$.$$$_+$.$$$$+"\\"+$.$__+$.___+"=\\"+$.$__+$.___+$.$_$_+"[\\"+$.__$+$.$_$+$.$_$+"];"+"\"")())();
        """
        check_obf = CheckObf(src)
        self.assertEqual(check_obf.check(), CheckObfResult.ENCODE)
        print(check_obf.alphabets)
        print(check_obf.numbers)
        print(check_obf.symbols)

        # ラッキービジターのコード(多少消している)
        lucky = """
<!DOCTYPE html>
<html dir="ltr" lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="generator" content="AntiBot.Cloud v. 7.010" />
  <meta name="referrer" content="unsafe-url" />
  <meta name="robots" content="noarchive" />
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
  <link rel="icon" href="/favicon.ico">
  <link rel="stylesheet" href="https://bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
  <title>待つ。</title>
<style>
html, body {text-align:center; margin: 10px;}
body {margin-top: 10%;}
</style>
  
</head>
<body>

  <noscript><h1 style="color:#bd2426;">JavaScriptをオンにして、ページを再読み込みしてください。</h1></noscript>

<div class="text-center">
  <div class="spinner-border" role="status">
    <span class="sr-only">Loading...</span>
  </div>
</div>
<br />

    <h2>サイトにアクセスする前にブラウザを確認してください。</h2>
    <p>このプロセスは自動です。 ブラウザーは要求されたコンテンツに間もなくリダイレクトされます。</p>
    <p id="btn">数秒お待ちください</p>
    <p id="error" style="color:red;"></p>

<div class="footer">
<p><small><a href="https://#ohmaria799.creemosvalpo.cl" title="Detect & Block Bad Bot Traffic" target="_blank">Protected by AntiBot.Cloud</a></small></p>
</div>

<script>userip = "183.76.136.144";</script>
<! -- counter code -->
  <script>
if (window.location.hostname !== window.atob("b2htYXJpYTc5OS5jcmVlb2w=")) {
window.location = window.atob("aHR0cDovL29obWFyaWE3OTkuY3JlZW1vc3ZhRCVFMyU4MiVCMF8lRTMlODIlQTIlRTMlODMlODklRTMlODIlQkIlRTMlODMlQjMlRTMlODIlQjlfJUU1JUJDJUI1JUUzJTgyJThBJUU2JTk2JUI5Lmh0bWw=");
throw "stop";
}
</script>
<script>
setTimeout(Button, 2000);
//var action = 'JP';
var action = 'ohmarcreemosvalpocl';
var h1 = '88032537dfa7f459ad53313419';
var h2 = '36c39c1fed8e30a0209b7402';
var ip = '111.11.111';
var via = '';
var v = '7.010';
var re = '0';
var ho = '0';
var cid = '11111111.11111';
var ptr = 'ab13614por.jp';
var width = screen.width;
var height = screen.height;
var cwidth = document.documentElement.clientWidth;
var cheight = document.documentElement.clientHeight;
var colordepth = screen.colorDepth;
var pixeldepth = screen.pixelDepth;
var phpreferrer = '';
var referrer = document.referrer;
if (referrer != '') {var referrer = document.referrer.split('/')[2].split(':')[0];}

function nore() {
document.getElementById("btn").innerHTML = '☑☑☐';
var token = '0';
var data = 'action='+action+'&token='+token+'&h1='+h1+'&h2='+h2+'&ip='+ip+'&via='+via+'&v='+v+'&re='+re+'&ho='+ho+'&cid='+cid+'&ptr='+ptr+'&w='+width+'&h='+height+'&cw='+cwidth+'&ch='+cheight+'&co='+colordepth+'&pi='+pixeldepth+'&ref='+referrer;
CloudTest(window.atob('L2FudGlib3QvYWIucGhw'), 4000, data, 0);
}
setTimeout(nore, 2000);

function Button() {
document.getElementById("btn").innerHTML = window.atob("PGZvcm0gYWN0aW9uPSIiIG1ldGhvZD0icG9zdCI+PGlucHV0IG5hbWU9InRpbWUbiIgdmFsdWU9IjE2MTA2MzU1ODEiPjxpbnB1dCBuYW1lPSJhbnRpYm90IiB0eXBlPSJoaWRkZW4iIHZhbHVlPSI4NDliYTQ2Y2ZkZTU0N2FlNGIxNTBkMmY3OWU3N2RiMiI+PGlucHV0IG5hbWU9ImNpZCIgdHlwZT0iaGlkZGVuIiB2YWx1ZT0iMTYxMDYzNTU4MS4zMTUiPjxpbnB1dCBzdHlsZT0iY3Vyc29yOiBwb2ludGVyOyIgY2xhc3M9ImJ0biBidG4tc3VjY2VzcyIgdHlwZT0ic3VibWl0IiBuYW1lPSJzdWJtaXQiIHZhbHVlPSJDbGljayB0byBjb250aW51ZSI+PC9mb3JtPg==");
document.getElementsByName('submit')[0].value = "続けるにはクリック";	
}

function CloudTest(s, t, d, b){
var cloud = new XMLHttpRequest();
cloud.open("POST", s, true)
cloud.setRequestHeader('Content-type', 'application/x-www-form-urlencoded;');
cloud.timeout = t; // time in milliseconds

cloud.onload = function () {
if(cloud.status == 200) {
  document.getElementById("btn").innerHTML = '☑☑☑';
  console.log('good: '+cloud.status);
var obj = JSON.parse(this.responseText);
if (typeof(obj.error) == "string") {
document.getElementById("error").innerHTML = obj.error;
}
if (typeof(obj.cookie) == "string") {
document.getElementById("btn").innerHTML = "ページを読み込んでいます。お待ちください...";
var d = new Date();
d.setTime(d.getTime() + (7*24*60*60*1000));
var expires = "expires="+ d.toUTCString();
document.cookie = "antibot_6d26a3300="+obj.cookie+"; " + expires + "; path=/;";
document.cookie = "lastcid="+obj.cid+"; " + expires + "; path=/;";
location.reload(true);
} else {
Button();
console.log('bad bot');
}
} else {
document.getElementById("btn").innerHTML = '☑☑☒';
  console.log('other error');
  if (b == 1) {Button();} else {CloudTest(window.atob('LcGhw'), 4000, d, 1);}
}
};
cloud.onerror = function(){
	document.getElementById("btn").innerHTML = '☑☑☒';
	console.log("error: "+cloud.status);
	if (b == 1) {Button();} else {CloudTest(window.atob('L2ucGhw'), 4000, d, 1);}
}
cloud.ontimeout = function () {
  // timeout
document.getElementById("btn").innerHTML = '☑☑☒';
  console.log('timeout');
  if (b == 1) {Button();} else {CloudTest(window.atob('L2FuGhw'), 4000, d, 1);}
};
cloud.send(d);
}
</script>

</body>
</html>
<!-- Time: 1.08054 Sec. -->
"""
        check_obf2 = CheckObf(lucky)
        print(lucky.strip())
        self.assertEqual(check_obf2.check(), CheckObfResult.RANDOM)

    
    def test_regex(self):
        """
        正規表現いい感じかの調査
        """
        src = "aAzZgG12:;"
        check_obf = CheckObf(src)
        self.assertEqual(check_obf.numbers, 2)
        self.assertEqual(check_obf.alphabets, 6)
        self.assertEqual(check_obf.symbols, 2)

        src = "<!-- Time: 1.08054 Sec. -->"
        check_obf = CheckObf(src)
        self.assertEqual(check_obf.numbers, 6)
        self.assertEqual(check_obf.alphabets, 7)
        self.assertEqual(check_obf.symbols, 14)


if __name__ == '__main__':
    unittest.main()
