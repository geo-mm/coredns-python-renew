import json
import os
import pathlib
import pytest
import shutil

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
            "allow": [],
            "deny": []
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
    os.environ["AUTH_TOKEN"] = TEST_AUTH_TOKEN
    os.environ["API_CONF_PATH"] = '{}/conf'.format(TEST_DATA_PATH)


def teardown_module(module):
    print("\n-------------- teardown after module --------------")
    shutil.rmtree(TEST_PROJECT_DATA_ROOT)


class TestAPIServer:

    @classmethod
    def setup_class(cls):
        print("------ setup api client ------")
        cls.client = testing.TestClient(createApp())

    @classmethod
    def teardown_class(cls):
        print("------ teardown after class TestSohu ------")

    @classmethod
    def _client(cls):
        return cls.client

    auth = {'Authorization': TEST_AUTH_TOKEN}

    def test_get_message(self):
        client = TestAPIServer._client()
        doc = {u'message': u'Hello!'}

        result = client.simulate_get('/', headers=self.auth)
        assert result.json == doc
