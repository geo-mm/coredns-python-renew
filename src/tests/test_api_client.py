import pytest
import responses
import argparse
import git
import pathlib
import json
import shutil

from dnstools_api_client.register_dns import register
from argparse import Namespace


def get_git_root(path):
    git_repo = git.Repo('.', search_parent_directories=True)
    return '{}/{}'.format(git_repo.git.rev_parse("--show-toplevel"), path)


TEST_PROJECT_DATA_ROOT = get_git_root('test_data')
TEST_AUTH_TOKEN = "MzRjY2ZlMWZkYmFkNDFiNWExZmQ1NTE2MTI2ZjA5M2VlZjhmYzQwNzg5ODlhMWFlYzA2N2ZhYTM2OTM4MWRhYWVlNWY0MTg4MzdiNjlhZGNjNjE4M2Q2NjFkNmQ1ZjZjY2VlMTA5MTFkYzhkZjk1NGU2YTU2ODNkMzMxYmY4NTI="

# TEST_AUTH_TOKEN
CONF_DATA = {
    "register": {
        "dev": {
            "ii.overflow.local": "10.0.45.77",
            "ii2.overflow.local": "10.0.46.79",
        },
        "intra": {
            "ii3.overflow.local": "10.0.45.11",
            "ii4.overflow.local": "10.0.46.11",
        }
    },
    "token": TEST_AUTH_TOKEN
}

TEST_CONF_PATH = TEST_PROJECT_DATA_ROOT + '/config.json'


def setup_module(module):
    print("\n-------------- setup before module --------------")
    # generate docker config and other configs
    # setup necessary environment variables
    pathlib.Path(TEST_PROJECT_DATA_ROOT).mkdir(parents=True, exist_ok=True)
    with open(TEST_CONF_PATH, mode='w') as fp:
        json.dump(CONF_DATA, fp)


def teardown_module(module):
    print("\n-------------- teardown after module --------------")
    shutil.rmtree(TEST_PROJECT_DATA_ROOT)


@responses.activate
def test_register_api():
    data = {'dev': {}, 'intra': {}}

    params = {}
    headers = {}

    def request_callback(request):
        payload = json.loads(request.body)
        params = payload
        headers = request.headers
        data[payload['namespace']][payload['host']] = payload['address']
        resp_body = data
        return (200, request.headers, json.dumps(data))

    responses.add_callback(
        responses.POST,
        'https://localhost:8000/register',
        callback=request_callback,
        content_type='application/json',
    )

    args = Namespace(url='https://localhost:8000', conf=TEST_CONF_PATH)

    register(args)

    assert len(responses.calls) == 4
    assert "ii.overflow.local" in data['dev'].keys()
    assert "10.0.45.77" == data['dev']["ii.overflow.local"]
    assert "ii2.overflow.local" in data['dev'].keys()
    assert "10.0.46.79" == data['dev']["ii2.overflow.local"]
    assert "ii.overflow.local" in data['dev'].keys()
    assert "10.0.45.11" == data['intra']["ii3.overflow.local"]
    assert "ii2.overflow.local" in data['dev'].keys()
    assert "10.0.46.11" == data['intra']["ii4.overflow.local"]


@responses.activate
def test_register_api_parameter_only():
    data = {'dev': {}, 'intra': {}}

    params = {}
    headers = {}

    def request_callback(request):
        payload = json.loads(request.body)
        params = payload
        headers = request.headers
        data[payload['namespace']][payload['host']] = payload['address']
        resp_body = data
        return (200, request.headers, json.dumps(data))

    responses.add_callback(
        responses.POST,
        'https://localhost:8000/register',
        callback=request_callback,
        content_type='application/json',
    )

    args = Namespace(
        url='https://localhost:8000',
        token=TEST_AUTH_TOKEN,
        namespace='dev',
        host='ii.overflow.local',
        address='10.0.45.78')

    register(args)

    assert len(responses.calls) == 1
    assert "ii.overflow.local" in data['dev'].keys()
    assert "10.0.45.78" == data['dev']["ii.overflow.local"]


@responses.activate
def test_register_api_override_by_params():
    data = {'dev': {}, 'intra': {}}

    params = {}
    headers = {}

    def request_callback(request):
        payload = json.loads(request.body)
        params = payload
        headers = request.headers
        data[payload['namespace']][payload['host']] = payload['address']
        resp_body = data
        return (200, request.headers, json.dumps(data))

    responses.add_callback(
        responses.POST,
        'https://localhost:8000/register',
        callback=request_callback,
        content_type='application/json',
    )

    args = Namespace(
        url='https://localhost:8000',
        conf=TEST_CONF_PATH,
        token=TEST_AUTH_TOKEN,
        namespace='dev',
        host='ii.overflow.local',
        address='10.0.45.78')

    register(args)

    assert len(responses.calls) == 4
    assert "ii.overflow.local" in data['dev'].keys()
    assert "10.0.45.78" == data['dev']["ii.overflow.local"]
    assert "ii2.overflow.local" in data['dev'].keys()
    assert "10.0.46.79" == data['dev']["ii2.overflow.local"]
    assert "ii.overflow.local" in data['dev'].keys()
    assert "10.0.45.11" == data['intra']["ii3.overflow.local"]
    assert "ii2.overflow.local" in data['dev'].keys()
    assert "10.0.46.11" == data['intra']["ii4.overflow.local"]
