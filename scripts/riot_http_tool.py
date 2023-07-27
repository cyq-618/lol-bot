import logging
import requests
from http_tool import send_http_request
from process_tool import kill_process_by_name


log = logging.getLogger(__name__)

null = None
true = True
false = False

"""
riot_http请求
"""


def send_riot_http_request(request_type, port, location, token, json=None):
    headers = {"Host": f"127.0.0.1:{port}",
               "Content-Type": "application/json",
               "Connection": "Keep-Alive",
               "Accept-Language": "en-US,en;q=0.9",
               "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                             "RiotClient/57.0.0 (CEF 74) Safari/537.36",
               "Authorization": f"Basic {token}",
               "Accept-Encoding": "gzip, deflate",
               "Referer": f"https://127.0.0.1:{port}/index.html"}
    try:
        return send_http_request(request_type, uri=f"https://127.0.0.1:{port}{location}", headers=headers, json=json)
    except requests.exceptions.RequestException as e:
        log.error(f"riot_http请求报错，内容为：{e}")
        print("riot_http请求报错")
        print(e)


"""
登录拳头客户端
"""


def riot_login(port, token, riot_username, riot_password):
    log.info("登录拳头客户端...")
    login_json1 = {"clientId": "riot-client", "trustLevels": ["always_trusted"]}
    login_json2 = {"username": riot_username, "password": riot_password, "persistLogin": False}
    res = send_riot_http_request("POST", port, "/rso-auth/v2/authorizations", token, login_json1)
    if res is None:
        log.warning({"登录请求第一步出错，具体信息为": res})
        return False
    # 如果404 500 返回错误
    if res.status_code > 299:
        log.warning({"登录请求第一步出错，具体信息为": res})
        return False
    res2 = send_riot_http_request("PUT", port, "/rso-auth/v1/session/credentials", token, login_json2)
    if res2 is None:
        log.warning({"登录请求第二步出错，具体信息为": res2})
        return False
    # 如果返回状态码不是201 返回错误
    if res2.status_code != 201:
        log.warning({"登录请求第二步出错，具体信息为": res2})
        return False
    return True


"""
退出登录拳头客户端
"""


def riot_logout(port, token):
    log.info("退出登录拳头客户端...")
    send_riot_http_request("DELETE", port, "/rso-auth/v1/session", token, {})


"""
关闭拳头客户端
"""


def riot_close(port, token):
    log.info("退出拳头客户端...")
    send_riot_http_request("POST", port, "/riot-client-lifecycle/v1/quit", token, {})
    kill_process_by_name("RiotClientServices.exe")
