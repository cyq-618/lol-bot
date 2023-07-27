import logging

import requests

log = logging.getLogger(__name__)

"""
http请求
"""


def send_http_request(request_type, uri, headers=None, json=None, verify=False):
    res = requests.request(request_type, url=uri, json=json, headers=headers, verify=verify)
    print("本次请求地址:", uri)
    print("发送的body:", json)  # res.request.body
    print("response返回结果：", res.text)
    print({"本次请求返回状态码": res.status_code})
    log.info({"本次请求地址": uri, "发送的body": json, "response返回结果": res.text, "本次请求返回状态码": res.status_code})
    return res
