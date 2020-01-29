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
