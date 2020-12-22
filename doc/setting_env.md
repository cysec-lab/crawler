# 環境設定

## ssdeep

ファジーハッシュをとるためのツール
pip のパスが自分の環境ではvenvになっているので `.env/bin/pip` を指定している

<https://python-ssdeep.readthedocs.io/en/latest/installation.html>

```bash
sudo apt-get install build-essential libffi-dev automake autoconf libtool
sudo BUILD_LIB=1 .env/bin/pip install ssdeep
```
