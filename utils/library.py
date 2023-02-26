# -*- encoding=utf8 -*-
__author__ = "tian.xin"

import json

import requests
from utils.config import config
from utils.logger import logger

log_status = config.get_log_status()


class API(object):
    """
  接口工具库
  """

    def __init__(self) -> None:
        pass

    @staticmethod
    def request(method, url, headers, request_json):
        """request 请求接口

    Parameters
    ----------
    method : str
        接口请求类型:post get put
    url : str
        接口路径
    headers : dict
        请求头
    request_json : str, json
        消息内容
    """
        response = requests.request(method, url, headers=headers, json=request_json, verify=False)
        if response.status_code != 200:
            tips_code = "{}接口：{} 响应异常！实际:{}".format(method, url, response.status_code)
            logger.warning(tips_code)
        elif log_status and response.status_code == 200:
            logger.info("=============================================")
            logger.info("====={}接口：{} 请求成功！=====".format(method, url))
            logger.info("Request headers:{}".format(headers))
            logger.info("Request Body:{}".format(request_json))
            logger.info("Status Code:{}".format(response.status_code))
            logger.info("Response Body:{}".format(response.text))
            return response
        elif not log_status and response.status_code == 200:
            return response

    @staticmethod
    def post(url, headers, request_json):
        """post post类型请求接口

        Parameters
        ----------
        url : str
            接口路径
        headers : dict
            请求头
        request_json : str, json
            消息内容
        """
        request_json = json.dumps(request_json)
        response = requests.post(url, headers=headers, data=request_json, verify=False)
        if response.status_code != 200:
            tips_code = "POST接口：{} 响应异常！实际:{}".format(url, response.status_code)
            logger.warning(tips_code)
            return None
        elif log_status and response.status_code == 200:
            logger.info("=============================================")
            logger.info("=====POST接口：{} 请求成功！=====".format(url))
            logger.info("Request headers:{}".format(headers))
            logger.info("Request Body:{}".format(request_json))
            logger.info("Status Code:{}".format(response.status_code))
            logger.info("Response Body:{}".format(response.text))
            return response
        elif not log_status and response.status_code == 200:
            return response


api = API()
