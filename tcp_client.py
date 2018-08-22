#!/usr/bin/env python
import sys
import logging
import socket
import struct
from threading import Event, Thread
import time

from util import *


logger = logging.getLogger('client')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
STOP = Event()


def accept(port):
    logger.info("trying to accept connection on port %s", port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP socket
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    s.bind(('', port))
    s.listen(1)
    s.settimeout(5)
    while not STOP.is_set():
        try:
            conn, addr = s.accept()
            logger.info("Accepted: port %s connected!", port)
            STOP.set()
        except socket.timeout:
            logger.info("accept on port %s timeout, retrying...", port)
            #time.sleep(1)
            continue


def connect(local_addr, addr):
    logger.info("connecting from %s to %s", local_addr, addr)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    s.bind(local_addr)
    while not STOP.is_set():
        try:
            s.connect(addr)
            logger.info("connected from %s to %s - success!", local_addr, addr)
            STOP.set()
        except socket.error:
            logger.info("connect to %s - socket error, retrying...", addr)
            time.sleep(1)
            continue
        # except Exception as exc:
        #     logger.exception("unexpected exception encountered")
        #     break


def main(known_server_host='54.187.46.146', known_server_port=5005):
    sa = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create socket
    sa.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sa.connect((known_server_host, known_server_port)) # connect to cloud-hosted server with known IP+port
    my_priv_addr = sa.getsockname() # get our own end of connection (ip+port), as we see it behind our NAT

    # 1. client->server. send client private_ip+port
    send_msg(sa, addr_to_msg(my_priv_addr))

    # 4. receive our public_ip+port
    data = recv_msg(sa) # receive our public IP+port seen outside of NAT
    logger.info("client %s %s - received data: %s", my_priv_addr[0], my_priv_addr[1], data)
    my_pub_addr = msg_to_addr(data)

    # 5. reply back to server with what we received from them
    send_msg(sa, addr_to_msg(my_pub_addr))

    # 7. receive peer address for the peer that the public server matched us with
    data = recv_msg(sa)
    pubdata, privdata = data.split(b'|')
    peer_pub_addr = msg_to_addr(pubdata)
    peer_priv_addr = msg_to_addr(privdata)
    logger.info(
        "my public is %s and private is %s, peer public is %s private is %s",
        my_pub_addr, my_priv_addr, peer_pub_addr, peer_priv_addr,
    )

    # try to both connect to the peer and accept connection from peer. whichever works faster. or works at all
    threads = {
        '0_accept': Thread(target=accept, args=(my_priv_addr[1],)),
        '1_accept': Thread(target=accept, args=(my_pub_addr[1],)),
        '2_connect': Thread(target=connect, args=(my_priv_addr, peer_pub_addr,)),
        '3_connect': Thread(target=connect, args=(my_priv_addr, peer_priv_addr,)),
    }
    for name in sorted(threads.keys()):
        logger.info('start thread %s', name)
        threads[name].start()

    while threads and not STOP.is_set():
        keys = list(threads.keys())
        for name in keys:
            try:
                threads[name].join(1)
            except Exception:
                continue
            if not threads[name].is_alive():
                threads.pop(name)

    if STOP.is_set():
        logger.info('connection to peer established! exiting')



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, message='%(asctime)s %(message)s')
    main(*addr_from_args(sys.argv))
