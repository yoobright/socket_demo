import socketserver
import struct
import json
import os
import socket
import threading
import time
import sys

from ctypes import *
from itertools import islice
from collections import deque

from head import AckHeader, TransHeader

MAX_MSG_SIZE = 1400

g_recv_queue = deque()
g_current_header = None
g_count_total = 0
g_count = 0

def socket_sevice():
    try:
        skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        skt.bind(('127.0.0.1', 6666))
        skt.listen(10)
    except socket.error as msg:
        print(msg)
        sys.exit(1)
    print('waiting connection...')

    while True:
        conn, addr = skt.accept()
        t = threading.Thread(target=deal_data, args=(conn, addr))
        t.start()
        # time.sleep(0.1)

def deal_data(conn, addr):
    print('Accept new connection from {0}'.format(addr))
    while True:
        recv_data = conn.recv(1024)
        if len(recv_data) > 0:
            [g_recv_queue.append(d) for d in recv_data]
            # print(g_recv_queue)

        print(len(g_recv_queue))

        global g_current_header
        if g_current_header is None and  len(g_recv_queue) >= 20:
            if g_recv_queue[0] == eval('0x01') and g_recv_queue[1] == eval('0x62'):
                print("AckHeader!!!")
                header_size = sizeof(AckHeader)
                test_data = list(islice(g_recv_queue, 0, header_size))                
                recv_header_data = struct.pack('{}B'.format(header_size), *test_data)
                print(recv_header_data)
                recv_header = AckHeader()
                memmove(addressof(recv_header), recv_header_data, header_size)
                print(recv_header.length)
                g_count_total = (recv_header.length + MAX_MSG_SIZE -1) // MAX_MSG_SIZE
                g_count = 0
                recv_header.client_id = 1
                send_data = string_at(addressof(recv_header), sizeof(recv_header))
                conn.send(send_data)

                [g_recv_queue.popleft() for i in range(header_size)]
            elif g_recv_queue[0] == eval('0x01') and g_recv_queue[1] == eval('0x61'):
                print("TransHeader!!!")
                header_size = sizeof(TransHeader)
                test_data = list(islice(g_recv_queue, 0, header_size))                
                recv_header_data = struct.pack('{}B'.format(header_size), *test_data)
                print(recv_header_data)
                recv_header = TransHeader()
                memmove(addressof(recv_header), recv_header_data, header_size)
                print("recv_header.data_size: {}".format(recv_header.data_size))
                g_current_header = recv_header

                [g_recv_queue.popleft() for i in range(header_size)]
            else:
                g_recv_queue.popleft()

        if g_current_header is not None:
            print("Process data!!!")
            data_size = g_current_header.data_size
            print("len(g_recv_queue): {}".format(len(g_recv_queue)))
            print("data_size: {}".format(data_size))
            if len(g_recv_queue) >= data_size:
                [g_recv_queue.popleft() for i in range(data_size)]
                g_count = g_count + 1
                print("g_count: {}, g_count_total: {}".format(g_count, g_count_total))
                
                if g_count == g_count_total:
                    send_data = string_at(addressof(g_current_header), sizeof(g_current_header))
                    conn.send(send_data)
                    g_count = 0
                    g_count_total = 0

                g_current_header = None
            


                
    print('exit ')

        

if __name__ == '__main__':
    socket_sevice()