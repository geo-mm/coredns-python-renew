import requests
import argparse
import json
import os


def register(args):
    if not (os.path.exists(args.conf)):
        return

    conf = {}

    with open(args.conf, mode='r') as fp:
        conf = json.load(fp)

    if (conf == None):
        return
    else:
        for k in ['token', 'register']:
            if not (k in conf.keys()):
                return

    headers = {'Authorization': conf['token']}

    for namespace in conf['register'].keys():
        dic = conf['register'][namespace]
        for item in dic.keys():
            j_data = {
                'namespace': namespace,
                'host': item,
                'address': dic[item]
            }
            resp = requests.post(args.url + '/register',
                                 headers=headers, json=j_data, verify=False)
            if (resp.status_code != 200):
                return


if __name__ == '__main__':
    (major, minor, a, b, c) = sys.version_info[:]

    parser = argparse.ArgumentParser(
        description='Register DNS service')
    parser.add_argument(
        '-c', '--conf', help='configuration file path', required=True)
    parser.add_argument('-u', '--url', help='server URL', required=True)

    args = parser.parse_args()
    if (args == None):
        parser.print_help()
    else:
        register(args)
