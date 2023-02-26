# -*- coding: utf-8 -*-
__author__ = "tian.xin"

import os
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

from iot_tcp.utils.config import config
from iot_tcp.utils.logger import logger
from iot_tcp.apis.auth_apis import auth_gateway

# 指定环境
os.environ['env'] = "system-dev"
# 定义一个后台任务非阻塞调度器
scheduler = BackgroundScheduler()
# 保存网关连接信息
dtu_connects = []
# 保存地面站连接信息
control_connects = []


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
        pass
    else:
        # 网关注册包校验
        logger.info(f"[注册包内容]{recv_data}")
        flag, result_data = auth_gateway(recv_data)
        if flag:
            client = threading.Thread(target=dtu_client_thread,
                                      args=(client_sock, client_addr, result_data['data']['gateway_id'],
                                            result_data['data']['gateway_key']))
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
    dtu_connects.append({'gateway_id': gateway_id,
                         'gateway_key': gateway_key,
                         'gateway_sock': client_sock})
    try:
        while True:
            recv_data = client_sock.recv(256)
            if recv_data:
                print(recv_data)
                # 发送给地面站数据显示模块
                for s in control_connects:
                    if s['gateway_key'] == gateway_key:
                        s['station_sock'].send(recv_data)
            else:
                for i in dtu_connects:
                    if i['gateway_sock'] == client_sock:
                        dtu_connects.remove(i)
                        break
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
    pass

def control_client_thread(client_sock, client_addr, gateway_key):
    """  地面站控制通信线程

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
    control_connects.append({'gateway_key': gateway_key, 'station_sock': client_sock})
    try:
        while True:
            recv_data = client_sock.recv(1024)
            if recv_data:
                print(recv_data)
                recv_data = eval(str(recv_data, encoding='utf-8'))
                send_flag = False
                for i in dtu_connects:
                    if i['gateway_key'] == recv_data['gateway_key']:
                        i['gateway_sock'].send(bytes(recv_data['command'], encoding='utf-8'))
                        send_flag = True
                if not send_flag:
                    logger.warning(f"[地面站控制]{recv_data['gateway_key']} 命令发送失败, 网关可能离线")
                    client_sock.send(bytes("0", encoding='utf-8'))
            else:
                client_sock.close()
                break
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
        logger.warn("[TCP Server]关闭服务器")
