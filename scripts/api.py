import base64

import requests
import urllib3
import logging
import client

from base64 import b64encode
from time import sleep
from constants import *
from scripts import utils
from scripts.process_tool import creat_process_by_name
from scripts.riot_http_tool import riot_logout

log = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Connection:
    def __init__(self):
        # LCU Vars
        self.lcu_host = LCU_HOST
        self.lcu_port = ''
        self.lcu_protocol = DEFAULT_PROTOCOL
        self.lcu_username = LCU_USERNAME
        self.lcu_password = ''
        self.lcu_session = ''
        self.lcu_headers = ''
        self.lcu_procname = ''
        self.lcu_pid = ''
        self.token = ''

    def init(self):
        log.info("正在获取游戏客户端连接")
        # Get Lockfile Data
        for timeout in range(31):
            if not os.path.isfile(LOCKFILE_PATH):
                if timeout == 30:
                    log.warning("League startup timeout. Cannot connect to LCU")
                    raise client.ClientError
                else:
                    sleep(1)
            else:
                lockfile = open(LOCKFILE_PATH, 'r')
                break

        lockfile_data = lockfile.read()
        log.debug(lockfile_data)
        lockfile.close()


        # Parse data for pwd
        lock = lockfile_data.split(':')
        self.lcu_procname = lock[0]
        self.lcu_pid = lock[1]
        self.lcu_port = lock[2]
        self.lcu_password = lock[3]
        self.lcu_protocol = lock[4]

        # Prepare Requests
        log.debug('{}:{}'.format(self.lcu_username, self.lcu_password))
        userpass = b64encode(bytes('{}:{}'.format(self.lcu_username, self.lcu_password), 'utf-8')).decode('ascii')
        self.token = userpass
        self.lcu_headers = {'Authorization': 'Basic {}'.format(userpass)}
        log.debug(self.lcu_headers['Authorization'])

        # Create Session
        self.lcu_session = requests.session()

        for i in range(15):
            sleep(1)
            r = self.request('get', '/lol-login/v1/session')
            if r.status_code != 200:
                log.info("连接请求失败: {}".format(r.status_code))
                continue

            if r.json()['state'] == 'SUCCEEDED':
                log.debug(r.json())
                log.info("连接请求成功\n")
                return
            else:
                log.info("游戏连接创建失败: {}".format(r.json()['state']))

        raise client.ClientError

    def request(self, method, path, query='', data=''):
        if not query:
            url = "{}://{}:{}{}".format(self.lcu_protocol, self.lcu_host, self.lcu_port, path)
        else:
            url = "{}://{}:{}{}?{}".format(self.lcu_protocol, self.lcu_host, self.lcu_port, path, query)

        log.debug("{} {} {}".format(method.upper(), url, data))

        fn = getattr(self.lcu_session, method)

        if not data:
            r = fn(url, verify=False, headers=self.lcu_headers)
        else:
            r = fn(url, verify=False, headers=self.lcu_headers, json=data)
        return r



class RiotConnection:
    def __init__(self):
        self.protocol = 'https'
        self.host = '127.0.0.1'
        self.port = ''
        self.toekn = ''
        self.headers = ''
        self.session = ''

    # 初始化拳头客户端连接
    def init(self):
        try:
            log.info("正在初始化拳头客户端 api")
            RiotClientUx_object = creat_process_by_name("RiotClientUx.exe")
            if RiotClientUx_object is None:
                log.info("RiotClientUx未找到...")
            RiotClientUx_cmdline = RiotClientUx_object.cmdline()
            RiotClientUx_port = RiotClientUx_cmdline[1].split('=')[1]
            RiotClientUx_token = RiotClientUx_cmdline[2].split('=')[1]
            RiotClientUx_token_base64 = base64.b64encode(bytes("riot:" + RiotClientUx_token, "utf-8")).decode("utf-8")
            self.token = RiotClientUx_token_base64
            self.port = RiotClientUx_port
            self.session = requests.session()
            self.headers = {"Host": f"127.0.0.1:{self.port}",
            "Content-Type": "application/json",
            "Connection": "Keep-Alive",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                        "RiotClient/57.0.0 (CEF 74) Safari/537.36",
            "Authorization": f"Basic {self.token}",
            "Accept-Encoding": "gzip, deflate",
            "Referer": f"https://127.0.0.1:{self.port}/index.html"}
        except:
            log.info("拳头客户端 api 初始化异常")



    def request(self, method, path, query='', data=''):
        if not query:
            url = "{}://{}:{}{}".format(self.protocol, self.host, self.port, path)
        else:
            url = "{}://{}:{}{}?{}".format(self.protocol, self.host, self.port, path, query)
        log.debug("{} {} {}".format(method.upper(), url, data))
        fn = getattr(self.session, method)
        if not data:
            r = fn(url, verify=False, headers=self.headers)
        else:
            r = fn(url, verify=False, headers=self.headers, json=data)
        return r


class SendGiftConnection():
    def __init__(self):
        self.protocol = 'https'
        self.host = '127.0.0.1'
        self.port = ''
        self.toekn = ''
        self.headers = ''
        self.session = ''

    def init(self, port, token):
        log.info("开始初始化送礼 api")
        self.toekn = token
        self.port = port
        self.session = requests.session()
        self.headers = {
            'Accept' : 'application/json' ,
            'Content-Type' : 'application/json',
            'User-Agent' : 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) LeagueOfLegendsClient/13.4.492.8133 (CEF 91) Safari/537.36',
            'AUTHORIZATION' : 'Bearer ' + token
        }
        log.info(" 送礼 api 初始化结束")

    def request(self, data, storeName):
        url = storeName + "/storefront/v3/gift?language=zh_CN"
        fn = getattr(self.session, "post")
        r = fn(url, verify=False, headers=self.headers, json=data)
        return r
