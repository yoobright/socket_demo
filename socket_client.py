import socket
import os
import sys
import time
import struct
from ctypes import *

from collections import deque, namedtuple
from enum import Enum

from head import AckHeader, TransHeader

MAX_MSG_SIZE = 1400

g_recv_queue = deque()
# g_status = None

class SendDesc():
    def __init__(self):
        self.status = None
        self.client_id = None
        self.count = None
        self.total_count = None
        self.data = None

g_send_desc = SendDesc()


class Status(Enum):
    IDLE = 1
    WAIT_START = 2
    TRNS = 3
    WAIT_DONE = 4
    

def get_file_data(file_name):
    if not os.path.isfile(file_name):
        print('file:{} is not exists'.format(file_name))
        return None
    
    with open(file_name, 'rb') as fp:
        file_data = fp.read()
        return file_data

def get_file_type_id(ext):
    if ext == ".jpg":
        return 1
    if ext == ".png":
        return 2
    if ext == ".bmp":
        return 3
    if ext == ".txt":
        return 4
    return None

def build_ack_data(data_type, data_size):
    h = AckHeader()
    h.header0 = eval('0x01')
    h.header1 = eval('0x62')
    h.length = data_size
    h.data_type = data_type
    chk_sum = h.header0 + h.header1
    for d in struct.pack("I", data_size):
        chk_sum = chk_sum + d
    h.chk_sum = chk_sum
    header_data = string_at(addressof(h), sizeof(h))
    return header_data

def get_send_size(offset, total_size):
    res_size = total_size - offset
    if res_size >= MAX_MSG_SIZE:
        return MAX_MSG_SIZE
    return res_size

def build_send_data(client_id, count, total_data):
    total_size = len(total_data)
    h = TransHeader()
    h.header0 = eval('0x01')
    h.header1 = eval('0x61')
    h.count = count
    h.client_id = client_id
    chk_sum = h.header0 + h.header1
    for d in struct.pack("I", count):
        chk_sum = chk_sum + d
    h.chk_sum = chk_sum

    offset = count * MAX_MSG_SIZE
    data_size = get_send_size(offset, total_size)
    h.data_size = data_size
    print("data_size: {}".format(data_size))
    header_data = string_at(addressof(h), sizeof(h))
    selected_data = total_data[offset:offset+data_size]
    payload_data = struct.pack('{}B'.format(data_size), *selected_data)
    data = header_data + payload_data 
    return data

def need_recv():
    return ((g_send_desc.status == Status.WAIT_START) or (g_send_desc.status == Status.WAIT_DONE))

def need_send():
    return g_send_desc.status == Status.TRNS

def socket_client():
    try:
        skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        skt.connect(('127.0.0.1', 6666))
    except socket.error as msg:
        print(msg)
        sys.exit(1)

    while True:
        file_name = input('> ')
        if file_name.strip() == "exit":
            break

        data = None
        file_type = get_file_type_id(os.path.splitext(file_name)[-1])

        if file_type is not None:
            data = get_file_data(file_name)
        
        if data is not None:
            total_size = len(data)
            print(total_size)
            ack_data = build_ack_data(file_type, total_size)
            skt.sendall(ack_data)
            
            g_send_desc.status = Status.WAIT_START
            g_send_desc.client_id = -1
            g_send_desc.count = 0
            g_send_desc.total_count = (total_size + MAX_MSG_SIZE -1) // MAX_MSG_SIZE
            g_send_desc.data = data

            while g_send_desc.status != Status.IDLE:
                print(len(g_recv_queue))
                print("status: {}".format(g_send_desc.status))
                if need_recv():
                    print("need_recv!!!")
                    recv_data = skt.recv(1024)
                    [g_recv_queue.append(d) for d in recv_data]
                
                if len(g_recv_queue) >= 20:
                    if g_recv_queue[0] == eval('0x01') and g_recv_queue[1] == eval('0x62'):
                        header_size = sizeof(AckHeader)
                        pop_data = [g_recv_queue.popleft() for i in range(header_size)]
                        recv_header_data = struct.pack('{}B'.format(header_size), *pop_data)
                        recv_header = AckHeader()
                        memmove(addressof(recv_header), recv_header_data, header_size)
                        if recv_header.client_id != eval('0xff'):
                            print("client_id: {}".format(recv_header.client_id))
                            g_send_desc.client_id = recv_header.client_id
                            g_send_desc.status = Status.TRNS                  

                    elif g_recv_queue[0] == eval('0x01') and g_recv_queue[1] == eval('0x61'):
                        header_size = sizeof(TransHeader)
                        pop_data = [g_recv_queue.popleft() for i in range(header_size)]
                        g_send_desc.status = Status.IDLE
                        g_send_desc.client_id = -1
                        g_send_desc.count = 0
                        g_send_desc.total_count = 0
                        g_send_desc.data = None
                    else:
                        [g_recv_queue.popleft() for i in range(2)]
                # else:
                #     g_send_desc.status = Status.WAIT_START
                
                if need_send():
                    print("need_send!!!")
                    send_data = build_send_data(g_send_desc.client_id, g_send_desc.count, g_send_desc.data)
                    skt.sendall(send_data)
                    g_send_desc.count = g_send_desc.count + 1
                    print(g_send_desc.count, g_send_desc.total_count)
                    if g_send_desc.count == g_send_desc.total_count:
                        print("send done!!!")
                        g_send_desc.status = Status.WAIT_DONE
  

    skt.close()

if __name__ == '__main__':
    socket_client()

