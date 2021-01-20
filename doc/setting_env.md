# 環境設定

## install

### python module

- ubuntuでpython3.5にpip
  - `apt-get install python3-setuptools`
  - `easy_install3 pip`
- ubuntuでpip3時にエラーが出るとき(python.hが見つからないよ的な)
- `sudo apt install python3-pip python3-dev`
- pip install
  - `pip install selenium mecab-python3 pyclamd psutil beautifulsoup4 scikit-learn`
  - beautifulsoup4
    - HTMLを解析するためのライブラリ
  - selenium
    - ヘッドレスブラウザを操作するためのライブラリ
  - mecab-python3
    - 文字列の形態素解析を行うためのライブラリ
  - pyclamd
    - ファイルの安全性を確かめるためのClamdAVを利用するためのライブラリ
  - psutil
    - クローラのプロセス状態を確認するために用るライブラリ
  - scikit-learn
    - 決定木で難読化JSをみつけるために使っているライブラリ

## ssdeep

ファジーハッシュをとるためのツール
pip のパスが自分の環境ではvenvになっているので `.env/bin/pip` を指定している

<https://python-ssdeep.readthedocs.io/en/latest/installation.html>

```bash
sudo apt-get install build-essential libffi-dev automake autoconf libtool
sudo BUILD_LIB=1 .env/bin/pip install ssdeep
```

### clamAV

```bash
sudo apt install -y clamav
sudo apt install -y clamav-daemon
sudo service clamav-daemon status
sudo service clamav-daemon restart
```

### mecab(neologd version)

<https://www.notion.so/itib/ba774e080a084581ac074f3c8ea879ab#a8dc9d6835374ae68a62fbdf52e7af28>

```bash
sudo apt-get install aptitude
sudo aptitude install mecab libmecab-dev mecab-ipadic-utf8 git make curl xz-utils file
git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git
./mecab-ipadic-neologd/bin/install-mecab-ipadic-neologd -n
pip install mecab-python3
```

neologdを使わないなら以下でいい

```bash
sudo apt-get install mecab libmecab-dev mecab-ipadic mecab-ipadic-utf8
pip install mecab-python3
```

- mecab-python3がインストールできない場合
  - このフォルダ内のmecab-python3の中身を/usr/local/lib/python3.5/dist-packagesに入れる
  - それでも無理なら、sudo apt install python3-devをする
- ipadicの記号がサ変になるのを解決
  - このフォルダ内のmecab_system_dicの中身を/etc/alternatives/mecab-dictionaryのファイルと入れ替える
  - (mecabの使用辞書の確認方法：mecab -D)

### geckodriver

```bash
sudo chmod +x geckodriver
sudo mv geckodriver /usr/local/bin
```

## 過去に使っていた者たち

いまはいらないが設定する際は参考に

### phantomjs

```bash
wget -O /tmp/phantomjs-2.1.1-linux-x86_64.tar.bz2 https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2
cd /tmp
bzip2 -dc /tmp/phantomjs-2.1.1-linux-x86_64.tar.bz2 | tar xvf -
sudo mv /tmp/phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/local/bin/
sudo apt-get install -y nodejs nodejs-legacy(if not exists)
```

### pycharm

- pycharmをdownload
  - 展開
    - `tar xvzf pycharm-community*.tar.gz -C /tmp/`
  - 移動
    - `sudo su -c "chown -R cysec:cysec /tmp/pycharm*"`
    - `sudo mv /tmp/pycharm-community* /opt/pycharm-community`

## crontab

定期実行を設定するサンプル

```bash
00 19 * * * /usr/bin/python3 /home/cysec/Desktop/crawler/src/operate_main.py ritsumeikan 1>>/home/cysec/Desktop/crawler/organization/ritsumeikan/log.log 2>>/home/cysec/Desktop/crawler/organization/ritsumeikan/er.log
00 18 * * * /usr/bin/python3 /home/cysec/Desktop/crawler/src/resources_observer.py 1>/home/cysec/Desktop/crawler/mem.log 2>&1
```
