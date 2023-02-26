# -*- encoding=utf8 -*-
__author__ = "tian.xin"

import os
import operator
from configparser import RawConfigParser

BASE_DIR = os.path.abspath(os.path.dirname(__file__)).split('utils')[0]

class Config(object):
    """
    读取配置文件
    """
    def __init__(self) -> None:
        # 工程文件路径
        self.project_path = BASE_DIR
        # 配置文件路径
        self._config_path = self.project_path + "setup.cfg"
        print(self._config_path)
        self.config_parser = RawConfigParser()
        self.config_parser.read(self._config_path, 'utf-8')  # 读取配置文件所有信息
    
    def get_config_data(self, option='', section='common_info'):
        """get_config_data 按条件返回某条 setup.cfg 值

        Parameters
        ----------
        section: str
            橙色标题名
        option: str
            参数名

        Returns
        -------
        value: str
            按条件返回某条 setup.cfg 值
        """
        return self.config_parser.get(section, option)
    
    def join_absolute_path(self, relative_path) -> str:
        """join_absolute_path 拼接全局路径

        Parameters
        ----------
        relative_path : str
            相对路径
            
        Returns
        ----------
        absolute_path: str
            拼接后的绝对路径
        """
        absolute_path = self.project_path + relative_path
        return absolute_path
    
    @staticmethod
    def get_base_url() -> str:
        """get_base_url 使用配置文件setup.cfg中的result_server地址作为全局接口的base url
        """
        base_url = config.get_config_data("result_server", section=os.environ.get("env"))
        if operator.eq(base_url[-1], "/"):
            base_url = base_url[:-1]
        return base_url
    
    @staticmethod
    def get_server_ip() -> str:
        """get_server_ip 获取配置文件中的监听ip
        """
        ip = config.get_config_data("ip", section=os.environ.get("env"))
        return ip
    @staticmethod
    def get_server_port() -> int:
        """get_server_ip 获取配置文件中的监听port
        """
        port = config.get_config_data("port", section=os.environ.get("env"))
        return int(port)
    
    @staticmethod
    def get_log_status():
        status = config.get_config_data("open", section="log")
        if status == "true":
            return True
        else:
            return False
        
config = Config()
