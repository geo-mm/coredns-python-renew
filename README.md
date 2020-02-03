# coredns-python-renew

因工作需求需要架個 DNS server 做測試, 對同一網域把 N 個不同網段的查詢導向不同 IP 位置. 目前想到的是使用 N 個 CoreDNS container bind 不同網段, 由一個 API Server 負責接收外部註冊 host name 並寫到 CoreDNS 的設定當中.

# 前期需求

請先安裝,

-   [docker](https://docs.docker.com/install/)
-   [docker-compose](https://docs.docker.com/compose/install/)
-   virtualenv
-   pip3
-   python3

# 使用方式

先 git clone 目前的 project, 並用下列的範例一個 `config` 檔案, eg: `gen_docker.conf`

```
{
    "interfaces": {
        "dev": {
            "host": "1.2.3.4",
            "dns": [ "1.1.1.1", "8.8.8.8" ]
        },
        "intra": {
            "host": "1.2.4.5",
            "dns": ["1.1.1.1", "8.8.8.8"]
        }
    },
    "address": {
        "allow": ["1.2.3.0/24", "1.2.4.0/24"]
    },
    "token": "xxxx"
}
```

-   "interfaces": 要綁定的 docker 介面
    -   "host": 綁定的 IP 位置
    -   "dns": 預設的 DNS 位置
-   "address":
    -   "allow": 允許註冊的 IP 位置範圍
-   "token": API Server 認證 Token, 可以以任何方式產生

執行下列指令,

```
virtualenv --python=python3 runenv
source runenv/bin/activate
pip3 install -r requirements.txt
cd src/local-dns-tools/dnstools_scripts
./gen_docker.py -c [CONF_PATH] -p [OUTPUT_DIR]
```

-   `CONF_PATH`: config 檔案路徑
-   `OUTPUT_DIR`: 輸出檔案路徑

產生 https ssl key,

```
cd [OUTPUT_DIR]/api
chmod +x entry.sh
openssl req -newkey rsa:2048 -nodes -keyout server.key -x509 -days 365 -out server.crt
```

執行 `docker-compose`,

```
cd [OUTPUT_DIR]
docker-compose up -d
```
