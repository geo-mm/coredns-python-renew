import argparse
import json
import os
import requests
import sys


def containAll(all, exam):
    return len(set(all) - set(exam)) == 0


def register(args):
    # if (args.conf == None):
    #     return False
    # if not (os.path.exists(args.conf)):
    #     return False

    register = {}
    token = None

    argDic = vars(args)

    if (('conf' in argDic.keys()) and (os.path.exists(args.conf))):
        with open(args.conf, mode='r') as fp:
            conf = json.load(fp)
            if ('register' in conf.keys()):
                register = conf['register']
            if ('token' in conf.keys()):
                token = conf['token']

    if ('token' in argDic.keys()):
        token = args.token

    #if ('namespace' in argDic.keys()) and ('host' in argDic.keys()):
    if (containAll(['namespace', 'host', 'address'], argDic)):
        if not (args.namespace in register.keys()):
            register[args.namespace] = {}
        register[args.namespace][args.host] = args.address

    headers = {'Authorization': token}

    for namespace in register.keys():
        dic = register[namespace]
        for item in dic.keys():
            j_data = {
                'namespace': namespace,
                'host': item,
                'address': dic[item]
            }
            resp = requests.post(
                args.url + '/register',
                headers=headers,
                json=j_data,
                verify=False)
            if (resp.status_code != 200):
                return False
    return True


if __name__ == '__main__':
    (major, minor, a, b, c) = sys.version_info[:]

    parser = argparse.ArgumentParser(description='Register DNS service')
    parser.add_argument('-c', '--conf', help='configuration file path')
    parser.add_argument('-u', '--url', help='server URL', required=True)
    parser.add_argument('-t', '--token', help='authorization token')
    parser.add_argument('-s', '--namespace', help='DNS namespace')
    parser.add_argument('-h', '--host', help='registered host name')
    parser.add_argument('-a', '--address', help='registered host address')

    args = parser.parse_args()
    if (args == None):
        parser.print_help()
    else:
        if not register(args):
            print('Parameter error')
            parser.print_help()
