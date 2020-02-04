# 動機

因工作需求需要架個 DNS server 做測試, 對同一網域把 N 個不同網段的查詢導向不同 IP 位置. 目前想到的是使用 N 個 CoreDNS container bind 不同網段, 由一個 API Server 負責接收外部註冊 host name 並寫到 CoreDNS 的設定當中.

# 使用方式

# Falcon

```sh
 docker run -it --rm -p 8000:8000 --entrypoint="/bin/bash" python:3.7-slim

pip install falcon gunicorn
# edit test.py with example
gunicorn -b 0.0.0.0:8000 test:app
```

```
docker run -d --name coredns-test -p 1053:53 -p 1053:53/udp -v `pwd`:/etc/coredns coredns/coredns -conf /etc/coredns/Corefile
# in project root
docker-compose -p coredns down
docker run -it -v `pwd`/src:/api --rm python:3.7-slim /bin/sh
```
