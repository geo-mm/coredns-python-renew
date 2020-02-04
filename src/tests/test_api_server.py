import json
import os
import pathlib
import pytest
import shutil
import re

from argparse import Namespace
from dnstools_api_server import createApp
from dnstools_scripts.gen_docker import generate
from dnstools_scripts.gen_docker import get_git_root
from falcon import testing

TEST_PROJECT_DATA_ROOT = get_git_root('test_data')
TEST_DATA_PATH = '{}/data'.format(TEST_PROJECT_DATA_ROOT)
TEST_CONFIG_FILE = '{}/gen_docker.conf'.format(TEST_PROJECT_DATA_ROOT)
TEST_AUTH_TOKEN = "MzRjY2ZlMWZkYmFkNDFiNWExZmQ1NTE2MTI2ZjA5M2VlZjhmYzQwNzg5ODlhMWFlYzA2N2ZhYTM2OTM4MWRhYWVlNWY0MTg4MzdiNjlhZGNjNjE4M2Q2NjFkNmQ1ZjZjY2VlMTA5MTFkYzhkZjk1NGU2YTU2ODNkMzMxYmY4NTI="


def create_testure_config():
    data = {
        "interfaces": {
            "dev": {
                "host": "10.0.45.82",
                "dns": ["1.1.1.1", "8.8.8.8"]
            },
            "intra": {
                "host": "10.0.46.7",
                "dns": ["1.1.1.1", "8.8.8.8"]
            }
        },
        "address": {
            "allow": ["10.0.45.0/24", "10.0.46.0/24"]
        },
        "token": TEST_AUTH_TOKEN
    }
    pathlib.Path(TEST_PROJECT_DATA_ROOT).mkdir(parents=True, exist_ok=True)
    with open(TEST_CONFIG_FILE, mode='w') as fp:
        json.dump(data, fp, indent=4)


def setup_module(module):
    print("\n-------------- setup before module --------------")
    create_testure_config()
    args = Namespace(path=TEST_DATA_PATH, conf=TEST_CONFIG_FILE)
    # generate docker config and other configs
    generate(args)
    # setup necessary environment variables


def teardown_module(module):
    print("\n-------------- teardown after module --------------")
    shutil.rmtree(TEST_PROJECT_DATA_ROOT)


class TestDockerConfigs:

    @classmethod
    def setup_class(cls):
        print("------ setup api client ------")

    @classmethod
    def teardown_class(cls):
        print("------ teardown after class TestSohu ------")

    def test_files_exist(self):
        API_CONF_PATH = '{}/conf'.format(TEST_DATA_PATH)
        assert os.path.exists(API_CONF_PATH + '/conf.json')
        assert os.path.exists(API_CONF_PATH + '/client.conf.json')
        assert os.path.exists(API_CONF_PATH + '/dev')
        assert os.path.exists(API_CONF_PATH + '/dev/Corefile')
        assert os.path.exists(API_CONF_PATH + '/dev/hosts')
        assert os.path.exists(API_CONF_PATH + '/intra')
        assert os.path.exists(API_CONF_PATH + '/intra/Corefile')
        assert os.path.exists(API_CONF_PATH + '/intra/hosts')


class TestAPIServer:

    @classmethod
    def setup_class(cls):
        print("------ setup api client ------")
        os.environ["AUTH_TOKEN"] = cls.AUTH_TOKEN
        os.environ["API_CONF_PATH"] = cls.API_CONF_PATH
        cls.client = testing.TestClient(createApp())
        assert os.path.exists(cls.HOST_CONF_PATH)

    @classmethod
    def teardown_class(cls):
        print("------ teardown after class TestSohu ------")

    @classmethod
    def _client(cls):
        return cls.client

    auth = {'Authorization': TEST_AUTH_TOKEN}
    AUTH_TOKEN = TEST_AUTH_TOKEN
    API_CONF_PATH = '{}/conf'.format(TEST_DATA_PATH)
    HOST_CONF_PATH = API_CONF_PATH + '/hosts.json'

    def test_get_message(self):
        client = TestAPIServer._client()
        doc = {'message': 'Hello!'}

        result = client.simulate_get('/', headers=self.auth)
        assert result.json == doc

    def test_register_api(self):
        client = TestAPIServer._client()
        host_name = 'ii.overflow.local'
        host_file = host_name.replace('.', '_') + '.conf'
        params = {
            'namespace': 'dev',
            'address': '10.0.45.77',
            'host': host_name
        }

        result = client.simulate_post(
            '/register', headers=self.auth, json=params)
        assert result.status_code in [200, 204]

        with open(self.HOST_CONF_PATH, 'r') as fp:
            host_data = json.load(fp)
            assert host_name in host_data['dev'].keys()

        host_full_path = '{}/dev/hosts/{}'.format(
            TestAPIServer.API_CONF_PATH, host_file)

        assert os.path.exists(host_full_path)

        with open(host_full_path, 'r') as fp:
            content = fp.read()
            result = re.search(
                r"[ |\t]*ii.overflow.local *{ *\n[ |\t]*hosts *{ *\n[ |\t]*10.0.45.77 *ii.overflow.local", content, re.MULTILINE)
            assert result != None

    def test_api_allow(self):
        client = TestAPIServer._client()
        host_name = 'ii2.overflow.local'
        host_file = host_name.replace('.', '_') + '.conf'
        params = {
            'namespace': 'dev',
            'address': '10.0.100.77',
            'host': host_name
        }

        result = client.simulate_post(
            '/register', headers=self.auth, json=params)
        assert not (result.status_code in [200, 204])

        with open(self.HOST_CONF_PATH, 'r') as fp:
            host_data = json.load(fp)
            assert not (host_name in host_data['dev'].keys())

        host_full_path = '{}/dev/hosts/{}'.format(
            TestAPIServer.API_CONF_PATH, host_file)

        assert not os.path.exists(host_full_path)
