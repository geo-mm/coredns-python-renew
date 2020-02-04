import argparse
import json
import os
import requests
import sys


def containAll(all, exam):
    for key in all:
        if not validArg(exam, key):
            return False
    return True
    #return len(set(all) - set(exam)) == 0


def validArg(dic, name):
    return (name in dic.keys()) and (dic[name] != None)


def dbgMsg(args, msg):
    argDic = vars(args)
    if validArg(argDic, 'debug'):
        print(msg)


def register(args):
    register = {}
    token = None

    argDic = vars(args)

    dbgMsg(args, 'parameters = {}'.format(argDic))

    if (('conf' in argDic.keys()) and (os.path.exists(args.conf))):
        with open(args.conf, mode='r') as fp:
            conf = json.load(fp)
            print('conf = {}'.format(conf))
            if validArg(conf, 'register'):
                register = conf['register']
            if validArg(conf, 'token'):
                token = conf['token']

    if validArg(argDic, 'token'):
        token = args.token

    if (containAll(['namespace', 'hostname', 'address'], argDic)):
        if not (args.namespace in register.keys()):
            register[args.namespace] = {}
        register[args.namespace][args.hostname] = args.address

    headers = {'Authorization': token}

    for namespace in register.keys():
        dic = register[namespace]
        for item in dic.keys():
            url = args.url + '/register'
            j_data = {
                'namespace': namespace,
                'host': item,
                'address': dic[item]
            }
            dbgMsg(
                args, 'url = {}, headers = {}, body = {}'.format(
                    url, headers, j_data))

            resp = requests.post(
                url, headers=headers, json=j_data, verify=False)
            if (resp.status_code != 200):
                dbgMsg(
                    args, 'resp = {}, body = {}'.format(resp.status_code,
                                                        resp.json))
                return False
    return True


if __name__ == '__main__':
    (major, minor, a, b, c) = sys.version_info[:]

    parser = argparse.ArgumentParser(description='Register DNS service')
    parser.add_argument('-c', '--conf', help='configuration file path')
    parser.add_argument('-u', '--url', help='server URL', required=True)
    parser.add_argument('-t', '--token', help='authorization token')
    parser.add_argument('-s', '--namespace', help='DNS namespace')
    parser.add_argument('-n', '--hostname', help='registered host name')
    parser.add_argument('-a', '--address', help='registered host address')
    parser.add_argument('-d', '--debug', help='debug message')

    args = parser.parse_args()
    if (args == None):
        parser.print_help()
    else:
        if not register(args):
            print('Parameter error')
            parser.print_help()
