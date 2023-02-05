#!/usr/bin/python3

# livebox API requester


import argparse
import ast
import logging
import pathlib
import re
import urllib

import requests


TIMEOUT = 10
URL = 'http://192.168.1.1'
CREDENTIALS = str(pathlib.Path(__file__).with_name('credentials'))
WAN_STATUS_FIELDS = ('WanState', 'LinkType', 'LinkState', 'GponState', 'MACAddress', 'Protocol', 'ConnectionState',
                     'LastConnectionError', 'IPAddress', 'RemoteGateway', 'DNSServers', 'IPv6Address')

LOG_LEVELS = ('info', 'warning', 'error', 'critical')
logging.basicConfig(level=logging.WARNING, format='%(name)s: %(message)s')
log = logging.getLogger('livebox')


class Livebox:
    def __init__(self, url: str, *, timeout: int = TIMEOUT):
        self.url = urllib.parse.urljoin(url, 'ws')  # TODO; check url
        if timeout <= 0:
            self.timeout = TIMEOUT
            log.warning(f'invalid network timeout ({timeout}), fallback to {TIMEOUT}')
        else:
            self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/x-sah-ws-4-call+json'})

    @staticmethod
    def decodeCredentials(credentials, *, _limit=2) -> (str | None, str | None):
        """decode credentials and return (login, password)"""
        try:
            decoded = ast.literal_eval(credentials)
        except (ValueError, SyntaxError):
            decoded = credentials

        match decoded:
            case {'login': str(), 'password': str()}:
                return decoded['login'], decoded['password']
            case (str(), str()):
                return decoded
            case str() | pathlib.Path if _limit > 0 and (path := pathlib.Path(decoded)).is_file():
                with open(path, 'r') as file:
                    return Livebox.decodeCredentials(file.read(1024), _limit=_limit-1)
            case _:
                log.error('failed to decode credentials')
                return '', ''

    def authenticate(self, credentials) -> bool:
        """authenticate using credentials"""
        login, password = self.decodeCredentials(credentials)

        try:
            response = self.session.post(
                url=self.url,
                headers={'Authorization': 'X-Sah-Login'},
                json={
                    'service': 'sah.Device.Information',
                    'method': 'createContext',
                    "parameters": {
                        "applicationName": "so_sdkut",
                        "username": login,
                        "password": password,
                    },
                },
                timeout=self.timeout,
            )
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
            log.error(f'authentication failed: network error')
            return False

        if response.ok:  # (data :=response.json()).get('status') == 0:
            log.debug(f'authenticated as {login}')
            contextID = response.json()['data']['contextID']
            self.session.headers.update({'X-Context': contextID})
            self.session.cookies.set(' sah/contextId', contextID)
            return True

        else:
            log.warning(f'authentication failed: invalid or denied')
            return False

    @property
    def info(self) -> dict:
        """return livebox info as dict"""
        try:
            response = self.session.post(
                url=self.url,
                json={
                    "service": "NMC",
                    "method": "getWANStatus",
                    "parameters": {},
                },
                timeout=self.timeout
            )
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
            log.error('info request failed: network error')
            return dict()

        if response.ok:
            return response.json()['data']
        else:
            log.error('info request failed: invalid or denied')
            return dict()


def run():
    parser = argparse.ArgumentParser(prog=__file__, description='livebox info requester')
    parser.add_argument('--url', type=str, default=URL, help=f'livebox url (usually {URL})')
    parser.add_argument('--credentials', type=str, default=CREDENTIALS, help='login/password from json file or string')
    parser.add_argument('--timeout', type=int, default=TIMEOUT, help='network timeout delay')
    cmds = parser.add_mutually_exclusive_group()
    cmds.add_argument('-ip', '--ipv4', action='store_const', const='IPAddress', dest='cmd', default=False, help='wan IPv4')
    cmds.add_argument('-ipv6', '--ipv6', action='store_const', const='IPv6Address', dest='cmd', default=False, help='wan IPv6')
    cmds.add_argument('--info', choices=WAN_STATUS_FIELDS, dest='cmd', default='IPAddress', help='get specific info')

    args = parser.parse_args()

    if args.cmd:
        livebox = Livebox(args.url, timeout=args.timeout)
        if livebox.authenticate(args.credentials):
            value = livebox.info.get(args.cmd)
            log.debug(f'{args.cmd}: {value}')
            print(value)
        else:
            exit(1)
    else:
        parser.print_help()


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        exit(1)
