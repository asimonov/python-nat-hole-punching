import logging
import socket
import sys
import time
from util import *
import random

logger = logging.getLogger()


def main(host='127.0.0.1', port=9999, role='S'):
    sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
    logger.info("connecting to p2p broker %s:%s", host, port)
    sock.sendto(b'0', (host, port))
    priv_addr = sock.getsockname()
    sock.close()

    logger.info("my socket end is {}".format(priv_addr))
    sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.bind(('0.0.0.0', priv_addr[1]))

    logger.info("waiting for peer address")
    data, addr = sock.recvfrom(1024)
    logger.info('received from addr %s, data %s', addr, data)
    peer_addr = msg_to_addr(data)
    logger.info('using peer addr %s', peer_addr)

    msg = 0
    while True:
        if role=='S':
            s = str(msg)
            bs = bytes(s)
            logger.info('sending to %s data: %s', peer_addr, bs)
            sock.sendto(bs, peer_addr)
            msg += 1
        else:
            data, addr = sock.recvfrom(1024)
            logger.info('received from addr %s data: %s', addr, data)

        t = random.randrange(0,1500) / 1000.
        logger.info('sleep for %s sec', t)
        time.sleep(t)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
