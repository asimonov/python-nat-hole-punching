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

        time.sleep(random.randrange(0,1500) / 1000)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    main(sys.argv[1], sys.argv[2], sys.argv[3])
