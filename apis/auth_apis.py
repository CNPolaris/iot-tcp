# -*- coding:utf-8 -*-
from iot_tcp.utils.config import config
from iot_tcp.apis.api_path import AUTH_GATEWAY
from iot_tcp.utils.library import api


def auth_gateway(access_key):
    """auth_gateway 验证网关密钥API

  Parameters
  ----------
  access_key : str
      网关密钥
  """
    url = config.get_base_url() + AUTH_GATEWAY
    headers = {
        "Content-type": "application/json"
    }
    request_json = {
        'access_key': access_key
    }
    response = api.post(url, headers, request_json)
    if response is not None:
        result_json = response.json()
        if result_json['code'] == 200:  # 网关密钥验证成功, 返回网关ID
            return True, result_json
        else:
            return False, None
    else:
        return False, None
