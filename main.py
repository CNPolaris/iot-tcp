# -*- coding: utf-8 -*-
__author__ = "tian.xin"

import os
import socket
import threading
import struct
import json
import time
from concurrent.futures import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

from utils.config import config
from utils.logger import logger
from apis.auth_apis import auth_gateway

# 指定环境
os.environ['env'] = "system-prod"
# 定义一个后台任务非阻塞调度器
scheduler = BackgroundScheduler()
# 保存网关连接信息
dtu_connects = {}
# 保存地面站连接信息
control_connects = {}
station_connects = {}


def client_handler(client_sock, client_addr):
    logger.info("--" * 40)
    logger.info("[收到新的客户端连接]处理连接")
    recv_data = client_sock.recv(65)
    recv_data = str(recv_data, encoding='utf-8')
    s_data = recv_data.split("&")
    if s_data[0] == "command":
        # 地面站控制模块建立连接
        control_client = threading.Thread(target=control_client_thread, args=(client_sock, client_addr, s_data[1]))
        control_client.start()
    elif s_data[0] == "station":
        station_client = threading.Thread(target=station_client_thread, args=(client_sock, client_addr, s_data[1]))
        # 地面站数据显示模块
        station_client.start()
    else:
        # 网关注册包校验
        logger.info(f"[注册包内容]{recv_data}")
        flag, result_data = auth_gateway(recv_data)
        if flag:
            client = threading.Thread(target=dtu_client_thread,
                                      args=(client_sock, client_addr, result_data['data']['gateway_id'],
                                            s_data[1]))
            client.start()
        else:
            client_sock.close()
            logger.error(f"[注册包信息异常]非法连接, 服务器主动断开连接=>{client_addr}")


def dtu_client_thread(client_sock, client_addr, gateway_id, gateway_key):
    """dtu_client_thread 处理DTU网关的线程

  Parameters
  ----------
  client_sock : socket
    负责DTU网关的socket
  client_addr : _type_
      _description_
  result_data : _type_
      _description_
  """
    logger.info(f"[注册包核验成功]合法连接, 新增子线程跟踪=>{client_sock}")
    dtu_connects[gateway_key] = client_sock
    try:
        while True:
            recv_data = client_sock.recv(256)
            if recv_data:
                if recv_data == b'yuanli':
                    break
                try:
                    station_connects[gateway_key].send(recv_data)
                except:
                    logger.error("[地面站-数据模块]网关发送数据错误")
            else:
                
                client_sock.close()
                break
    except:
        client_sock.close()
        pass

def station_client_thread(client_sock, client_addr, gateway_key):
    """station_client_thread 地面站数据显示线程处理

    Parameters
    ----------
    client_sock : _type_
        _description_
    client_addr : _type_
        _description_
    gateway_key : _type_
        _description_
    """
    station_connects[gateway_key] = client_sock
    try:
        while True:
            header_len = struct.unpack('i', client_sock.recv(4))[0]
            #收报头
            header_bytes = client_sock.recv(header_len) #收过来的也是bytes类型
            header_json = header_bytes.decode('utf-8')   #拿到json格式的字典
            header_dic = json.loads(header_json)  #反序列化拿到字典了
            total_size = header_dic['total_size']  #就拿到数据的总长度了
            recv_data = client_sock.recv(total_size)
            
            if recv_data == b'-1':
              logger.info("[地面站-数据接收模块]主动关闭连接")
              del station_connects[gateway_key]
              client_sock.close()
              break
            
    except:
        logger.error("[地面站-数据模块]通信出错")
    

def control_client_thread(client_sock, client_addr, gateway_key):
    """地面站控制通信线程

    Parameters
    ----------
    client_sock: socket
        负责当前通信地面站的socket
    client_addr: socket
        当前地面站地址
        
    Returns
    -------

    """
    logger.info(f"[地面站连接], socket: {client_addr}, gateway: {gateway_key}")
    control_connects[gateway_key] = client_sock
    try:
        while True:
            header_len = struct.unpack('i', client_sock.recv(4))[0]
            #收报头
            header_bytes = client_sock.recv(header_len) #收过来的也是bytes类型
            header_json = header_bytes.decode('utf-8')   #拿到json格式的字典
            header_dic = json.loads(header_json)  #反序列化拿到字典了
            total_size = header_dic['total_size']  #就拿到数据的总长度了
            recv_data = client_sock.recv(total_size)
            if recv_data == b'-1':
              logger.info("[地面站-控制模块]主动关闭连接")
              del control_connects[gateway_key]
              client_sock.close()
              break
            try:
              dtu_connects[gateway_key].send(recv_data)
              time.sleep(0.05)
            except:
              logger.warning('[地面站-控制模块]网关不在线')
    except:
        client_sock.close()
        pass


if __name__ == "__main__":
    # 创建服务器, 端口不支持复用
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 绑定端口, 打印运行信息
    server_address = (config.get_server_ip(), config.get_server_port())
    server_socket.bind(server_address)
    logger.info("==" * 40)
    logger.info(f'TCP Server starting up on port {server_address}')
    # 设置socket为被动连接
    server_socket.listen(1024)
    # 线程池
    pool = ThreadPoolExecutor(max_workers=8)
    # 开启任务调度
    scheduler.start()

    try:
        while True:
            # 主进程只负责监听新的客户连接
            logger.info(f'Main Thread [{threading.current_thread().name}], 正在等待客户端连接...')
            # client_sock是专门为这个客户端服务的socket, client_addr是包含客户端的ip和port的元组
            client_sock, client_addr = server_socket.accept()
            logger.info(f'Main Thread [{threading.current_thread().name}], client {client_addr} 已连接')
            # 将网关socket连接提交到线程池
            pool.submit(client_handler, client_sock, client_addr)
    except Exception as e:
        # 异常结束
        logger.error("[TCP Server] Error, Close Server")
    finally:
        # 关闭监听socket, 不再响应其他客户端连接
        server_socket.close()
        logger.warning("[TCP Server]关闭服务器")
