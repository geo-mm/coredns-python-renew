#!/bin/sh

install_pkgs() {
    res=`pip3 list --format columns | awk '{ print $1 }' | grep $1 | wc -l`

    if [ $res -eq 0 ]; then
        echo "=== Install $1"
        echo "pip3 install --no-cache-dir $1"
    fi
}

pkgs="gunicorn falcon"

for i in $pkgs; do
    install_pkgs $i
done

gunicorn --certfile=/api/server.crt --keyfile=/api/server.key -b 0.0.0.0:8000 api:app