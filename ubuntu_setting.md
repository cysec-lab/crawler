# Ubuntu setting

Ubuntuがとびまくっていたので、Ubuntuを入れなおした時に環境構築するために書いていたメモ。

## install

### python module

- ubuntuでpython3.5にpip
  - `apt-get install python3-setuptools`
  - `easy_install3 pip`
- ubuntuでpip3時にエラーが出るとき(python.hが見つからないよ的な)
    - `sudo apt install python3-pip python3-dev`
- pip install
  - selenium
  - mecab-python3
  - pyclamd
  - psutil
  - (matplotlib)

### pycharm

- pycharmをdownload
  - 展開
    - `tar xvzf pycharm-community*.tar.gz -C /tmp/`
  - 移動
    - `sudo su -c "chown -R cysec:cysec /tmp/pycharm*"`
    - `sudo mv /tmp/pycharm-community* /opt/pycharm-community`

### clamAV

```
sudo apt install -y clamav
sudo apt install -y clamav-daemon
sudo service clamav-daemon status
sudo service clamav-daemon restart
```

### phantomjs

現在は使っていないもの

```
wget -O /tmp/phantomjs-2.1.1-linux-x86_64.tar.bz2 https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2
cd /tmp
bzip2 -dc /tmp/phantomjs-2.1.1-linux-x86_64.tar.bz2 | tar xvf -
sudo mv /tmp/phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/local/bin/
sudo apt-get install -y nodejs nodejs-legacy(if not exists)
```

### mecab(neologd version)

https://www.notion.so/itib/ba774e080a084581ac074f3c8ea879ab#a8dc9d6835374ae68a62fbdf52e7af28

```
sudo apt-get install aptitude
sudo aptitude install mecab libmecab-dev mecab-ipadic-utf8 git make curl xz-utils file
git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git
./mecab-ipadic-neologd/bin/install-mecab-ipadic-neologd -n
pip install mecab-python3
```

neologdを使わないなら以下でいい

```
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

```
sudo chmod +x geckodriver
sudo mv geckodriver /usr/local/bin
```

## crontab

```
00 19 * * * /usr/bin/python3 /home/cysec/Desktop/crawler/src/operate_main.py ritsumeikan 1>>/home/cysec/Desktop/crawler/organization/ritsumeikan/log.log 2>>/home/cysec/Desktop/crawler/organization/ritsumeikan/er.log
00 18 * * * /usr/bin/python3 /home/cysec/Desktop/crawler/src/resources_observer.py 1>/home/cysec/Desktop/crawler/mem.log 2>&1
```
