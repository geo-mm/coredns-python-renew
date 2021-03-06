#!/usr/bin/env python3

import argparse
import copy
import git
import json
import os
import os
import pathlib
import sys

from distutils.dir_util import copy_tree
from distutils.file_util import copy_file
from ruamel.yaml import YAML

COREDNS_ROOT_CONF = """
.  {
    #chaos
    #whoami
    import /etc/coredns/hosts/*
    reload 10s
    forward . ##DNS##
    #log
    #errors
}

#import hosts/*
#reload 3
"""

CLIENT_CONF_DATA = {"register": {}, "token": ""}


def get_git_root(path):
    git_repo = git.Repo('.', search_parent_directories=True)
    return '{}/{}'.format(git_repo.git.rev_parse("--show-toplevel"), path)


def create_coredns_conf(name, host):
    return {
        'image': 'coredns/coredns:latest',
        'restart': 'always',
        'entrypoint': ['/coredns', '-conf', '/etc/coredns/Corefile'],
        'ports': ['{}:53:53'.format(host), '{}:53:53/udp'.format(host)],
        'volumes': ['conf/{}:/etc/coredns'.format(name)]
    }


def gen_root_corefile(dns=['8.8.8.8']):
    return COREDNS_ROOT_CONF.replace('##DNS##', ' '.join(dns))


def create_yam_conf(args, token):
    dest = {
        'version': '2',
        'services': {
            'api': {
                'image': 'python:3-alpine',
                'restart': 'always',
                'volumes': ['api:/api', 'conf:/api/conf'],
                'environment': ['AUTH_TOKEN={}'.format(token)],
                'working_dir': '/api',
                'port': ['443:8000'],
                'entrypoint': '/api/entry.sh'
            }
        }
    }

    if (len(args) == 0):
        return dest

    for i in args:
        print(i)
        (n, h) = i
        dest['services']['coredns-{}'.format(n)] = create_coredns_conf(n, h)

    return dest


def generate(args):
    # create path
    root_path = '.' if args.path == None else args.path
    c_path = './gen_docker.conf' if args.conf == None else args.conf

    with open(c_path) as fp:
        conf = json.load(fp)

    print(conf)

    api_path = '{}/api'.format(root_path)
    conf_path = '{}/conf'.format(root_path)
    yaml_conf = []

    print(api_path)

    try:
        pathlib.Path(api_path).mkdir(parents=True, exist_ok=True)
        inf = conf["interfaces"]
        for k in inf.keys():
            h = inf[k]['host']
            c_k_path = '{}/{}'.format(conf_path, k)
            h_path = '{}/hosts'.format(c_k_path, k)
            core_path = '{}/Corefile'.format(c_k_path)
            yaml_conf.append((k, h))
            print(h_path)
            pathlib.Path(h_path).mkdir(parents=True, exist_ok=True)
            default_file = '{}/default'.format(h_path)
            with open(default_file, mode='w', encoding="utf-8") as fp:
                fp.write('\n')
            with open(core_path, mode='w', encoding="utf-8") as fp:
                fp.write(gen_root_corefile(inf[k]['dns']))

    except Exception as e:
        print('Failed to create path {}, exit'.format(root_path))
        print(e)
        sys.exit(1)

    yaml = YAML()
    yaml.default_flow_style = False
    auth_token = conf['token']
    docker = create_yam_conf(yaml_conf, auth_token)
    docker_file = '{}/docker-compose.yaml'.format(root_path)
    client_conf_file = '{}/client.conf.json'.format(conf_path)

    with open(docker_file, mode='w') as fp:
        yaml.dump(docker, fp)

    # copy server files to dest
    server_path = get_git_root('src/local-dns-tools/dnstools_api_server')
    copy_tree(server_path, api_path)
    copy_file(c_path, '{}/conf.json'.format(conf_path))

    with open(client_conf_file, mode='w') as fp:
        client_conf = copy.deepcopy(CLIENT_CONF_DATA)
        client_conf['token'] = auth_token
        json.dump(client_conf, fp, indent=4)


def create(args):
    print(args)


if __name__ == '__main__':
    (major, minor, a, b, c) = sys.version_info[:]

    if major < 3 or minor < 5:
        print('You need at leasts python 3.5 to run the script')
        exit(1)

    parser = argparse.ArgumentParser(
        description='Docker-compose generator for customized DNS service')

    subparsers = parser.add_subparsers(help='Sub-command list', dest='command')
    cmd_generate = subparsers.add_parser(
        'generate', help='generate base configuration')
    '''
    cmd_generate.add_argument('-c', '--conf', action='append',
                            help='<Required> configuration with interface, eg: abc/0.0.0.0', required=True)
    '''
    #cmd_generate.add_argument('--conf_path', help='configuration file path')
    cmd_generate.add_argument('-c', '--conf', help='configuration file path')
    cmd_generate.add_argument(
        '-p', '--path', help='destination path, default is current directory')

    cmd_create = subparsers.add_parser(
        'create', help='create  startup/shutdown scripts')
    cmd_create.add_argument(
        '-d',
        '--destination',
        action='append',
        help='<Required> destination DNS host',
        required=True)
    cmd_create.add_argument(
        '-n',
        '--hostname',
        action='append',
        help='<Required> hostname to register',
        required=True)

    args = parser.parse_args()
    if (args == None):
        parser.print_help()
        #print(parser.parse_args(['generate', '--help']))
    elif (args.command == 'generate'):
        generate(args)
    elif (args.command == 'create'):
        create(args)
    else:
        parser.print_help()
