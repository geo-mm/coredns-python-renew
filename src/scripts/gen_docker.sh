#!/usr/bin/env bash

result = `python3 -c 'import sys; (major, minor, a, b, c) = sys.version_info[:]; print("true" if major >= 3 and minor >= 5 else "false")'`

if [[ result == 'false' ]]; then
    echo "You need python version 3.5 and up to run the script"
    exit 1
fi

runtime_path=`pwd`/run_env

if [ ! -d './run_env' ]; then
    virtualenv run_env
    $runtime_path/bin/activate
    pip3 install ruamel.yaml
    ./gen_docker.py "$@"
fi


