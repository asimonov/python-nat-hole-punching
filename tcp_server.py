#!/usr/bin/env python
import sys
import logging
import socket
import struct
import fcntl
import os
from util import *


logger = logging.getLogger()
clients = {}


def main(host='0.0.0.0', port=5005):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create TCP socket to listen on
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port)) # bind to specified port
    s.listen(1) # start listening
    s.settimeout(30)

    while True:
        try:
            conn, addr = s.accept() # accept an incoming connection. record client ip+port
        except socket.timeout:
            continue

        logger.info('connection address: %s', addr) # print public client IP+port

        # 2. receive client private_ip+port
        data = recv_msg(conn)
        priv_addr = msg_to_addr(data)

        # 3. server->client. send client its public ip+port
        send_msg(conn, addr_to_msg(addr))

        # 6. receive what we just sent to make sure it is compatible client
        data = recv_msg(conn)
        logger.info('server - received data: %s', data)
        data_addr = msg_to_addr(data)
        if data_addr == addr:
            logger.info('client reply matches. adding client to pool')
            # define Client object
            clients[addr] = Client(conn, addr, priv_addr)
        else:
            logger.info('client reply did not match')
            # something weird connected. close connection
            conn.close()

        # peers matching logic
        if len(clients) == 2:
            (addr1, c1), (addr2, c2) = clients.items()
            logger.info('server - send client info to: %s', c1.pub)
            send_msg(c1.conn, c2.peer_msg())
            logger.info('server - send client info to: %s', c2.pub)
            send_msg(c2.conn, c1.peer_msg())
            clients.pop(addr1)
            clients.pop(addr2)

    conn.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    main(*addr_from_args(sys.argv))
