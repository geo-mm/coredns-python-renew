import falcon
import os
import json
import copy
import re
from ipaddress import IPv4Address, IPv4Network

AUTH_TOKEN = ''
CONF_PATH = ''
HOST_RECORDS_FILE = ''
CONF_FILE = ''
gConf = {}
gHosts = {}
gRestrict = []


def read_json_file(path):
    try:
        with open(path, mode='r') as fp:
            c = json.load(fp)
            return c
    except:
        print('Failed to open config file {}'.format(path))
        return None


def write_json_file(conf, path):
    try:
        with open(path, mode='w') as fp:
            json.dump(conf, fp, indent=4)
            return True
    except:
        print('Failed to write to config file {}'.format(path))
        return False


#
# ###HOST_NAME### {
#    hosts {
#        ###ADDRESS### ###HOST_NAME###
#        fallthrough
#    }
# }

DNS_REC_TEMPLATE_HEADER = """
hosts {
"""

DNS_REC_TEMPLATE_FOOTER = """
    fallthrough
}
"""


def write_host_with_namespace(namespace, records):
    try:
        filePath = '{}/{}/hosts/default'.format(CONF_PATH, namespace)
        with open(filePath, 'w') as fp:
            #fp.write(template)
            fp.write(DNS_REC_TEMPLATE_HEADER)
            for hostname in records.keys():
                fp.write('    {} {}'.format(records[hostname], hostname))
            fp.write(DNS_REC_TEMPLATE_FOOTER)
        
        #for hostname in records.keys():
            #fileName = '{}.conf'.format(hostname.replace('.', '_'))
            # filePath = '{}/{}/hosts/{}'.format(CONF_PATH, namespace, fileName)
            # with open(filePath, 'w') as fp:
            #     template = DNS_REC_TEMPLATE.replace('###HOST_NAME###',
            #                                         hostname).replace(
            #                                             '###ADDRESS###',
            #                                             records[hostname])
            #     fp.write(template)
    except Exception as e:
        print('Failed to update DNS record in [{}]: e'.format(namespace, e))
        return False


def read_conf():
    return read_json_file(CONF_FILE)


def read_host_conf():
    return read_json_file(HOST_RECORDS_FILE)


def write_host_conf(conf):
    return write_json_file(conf, HOST_RECORDS_FILE)


class TestRequest(object):

    def on_get(self, req, resp):
        """Handles GET requests"""
        resp.status = falcon.HTTP_200  # This is the default status
        resp.body = ('{"message" : "Hello!"}')


def check_tags(tags, dict):
    for t in tags:
        if not (t in dict):
            return False
    return True


def add_host_to_namespace(hosts, namespace, host, address):
    if not (namespace in hosts):
        return False
    if not (re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", address)):
        return False
    hosts[namespace][host] = address
    return True


class RegisterHost(object):

    def _invalid_parameter(self, resp):
        resp.status = falcon.HTTP_400
        resp.body = ('{"message" : "Invalid parameter"}')

    def _server_error(self, resp, msg):
        resp.status = falcon.HTTP_501
        resp.body = ('{"message" : "{}"}'.format(msg))

    def on_post(self, req, resp):
        global gConf
        global gHosts

        args = req.context.doc

        if not check_tags(['namespace', 'host', 'address'], args):
            self._invalid_parameter(resp)
            return

        if len(gRestrict) > 0:
            validAddr = False
            for ip_range in gRestrict:
                result = IPv4Address(args['address']) in ip_range
                print('address = {}, range = {}, result = {}'.format(
                    args['address'], str(ip_range), result))
                if (IPv4Address(args['address']) in ip_range):
                    validAddr = True
                    break
            if not validAddr:
                print('{} not Valid'.format(args['address']))
                self._invalid_parameter(resp)
                return

        oldRec = copy.deepcopy(gHosts)
        newRec = copy.deepcopy(gHosts)

        if not add_host_to_namespace(newRec, args['namespace'], args['host'],
                                     args['address']):
            _invalid_parameter(resp)
            return

        modified = False

        for namespace in oldRec.keys():
            # handle changes in namespace
            if (json.dumps(oldRec[namespace]) != json.dumps(newRec[namespace])):
                modified = True
                write_host_with_namespace(namespace, newRec[namespace])

        gHosts = newRec

        if (modified) and not write_host_conf(gHosts):
            _invalid_parameter(resp, 'failed to write host data')
            return

        resp.status = falcon.HTTP_200
        resp.body = (json.dumps(gHosts))


class ListHost(object):

    def on_get(self, req, resp):
        global gHosts
        if (gHosts != None):
            resp.status = falcon.HTTP_200  # This is the default status
            resp.body = (json.dumps(gHosts))
        else:
            resp.status = falcon.HTTP_503  # Host data is not ready
            resp.body = ('{"message": "host data does not exist or corrupted"}')


class AuthMiddleware(object):

    def process_request(self, req, resp):
        token = req.get_header('Authorization')

        if token is None:
            description = ('Please provide an auth token '
                           'as part of the request.')

            raise falcon.HTTPUnauthorized('Auth token required', description,
                                          None)

        if not self._token_is_valid(token):
            description = ('The provided auth token is not valid. '
                           'Please request a new token and try again.')

            raise falcon.HTTPUnauthorized('Authentication required',
                                          description, None)

    def _token_is_valid(self, token):
        return token == AUTH_TOKEN


class RequireJSON(object):

    def process_request(self, req, resp):
        if not req.client_accepts_json:
            raise falcon.HTTPNotAcceptable(
                'This API only supports responses encoded as JSON.')

        if req.method in ('POST', 'PUT'):
            if 'application/json' not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType(
                    'This API only supports requests encoded as JSON.')


class JSONTranslator(object):
    # NOTE: Starting with Falcon 1.3, you can simply
    # use req.media and resp.media for this instead.

    def process_request(self, req, resp):
        # req.stream corresponds to the WSGI wsgi.input environ variable,
        # and allows you to read bytes from the request body.
        #
        # See also: PEP 3333
        if req.content_length in (None, 0):
            # Nothing to do
            return

        body = req.stream.read(req.content_length or 0)
        if not body:
            raise falcon.HTTPBadRequest('Empty request body',
                                        'A valid JSON document is required.')

        try:
            req.context.doc = json.loads(body.decode('utf-8'))

        except (ValueError, UnicodeDecodeError):
            raise falcon.HTTPError(
                falcon.HTTP_753, 'Malformed JSON',
                'Could not decode the request body. The '
                'JSON was incorrect or not encoded as '
                'UTF-8.')

    def process_response(self, req, resp, resource, req_succeeded):
        if not hasattr(resp.context, 'result'):
            return

        resp.body = json.dumps(resp.context.result)


def envInit():
    global AUTH_TOKEN
    global CONF_PATH
    global HOST_RECORDS_FILE
    global CONF_FILE
    global gConf
    global gHosts
    global gRestrict

    AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
    CONF_PATH = os.environ.get('API_CONF_PATH')

    if (CONF_PATH == None):
        CONF_PATH = '/api/conf'

    HOST_RECORDS_FILE = '{}/hosts.json'.format(CONF_PATH)
    CONF_FILE = '{}/conf.json'.format(CONF_PATH)

    if (AUTH_TOKEN == None):
        AUTH_TOKEN = 'ZGJjN2ZkYjYwNWQ3ODJiOGUyMDEyMTQ2YmQ0YTJjZDcwY2ViNGUyZGRjNDZiMTRjZTBmMTc0MWZkNWU2M2Q0NTY5YmU0NTg2OGUxZjgzYzllNTBhMTllM2RiOTVlNzIxYWU2YzA0ZTYzZDViYWI2OWE0MzRlMjRiYmYyZWY3ODk='

    gConf = read_conf()

    if (gConf == None):
        print('Failed to read config files. Exit')
        exit(1)

    print(gConf['address']['allow'])
    print(type(gConf['address']['allow']))
    if ('address' in gConf.keys()) and ('allow' in gConf['address'].keys(
    )) and (gConf['address']['allow'] != None):
        for ip in gConf['address']['allow']:
            print(ip)
            gRestrict.append(IPv4Network(ip))

    gHosts = read_host_conf()

    if (gHosts == None):
        gHosts = {}

        for k in gConf['interfaces']:
            gHosts[k] = {}

        ans = write_host_conf(gHosts)
        if not ans:
            print('Failed to write to default host config file. Exit')
            exit(1)


def createApp():
    # falcon.API instances are callable WSGI apps
    app = falcon.API(middleware=[
        AuthMiddleware(),
        RequireJSON(),
        JSONTranslator(),
    ])

    envInit()

    register = RegisterHost()
    test = TestRequest()

    app.add_route('/', test)
    app.add_route('/register', register)

    return app
