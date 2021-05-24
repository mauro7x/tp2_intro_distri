from socket import (SOL_SOCKET, SO_REUSEADDR, socket,
                    AF_INET, SOCK_DGRAM, SHUT_RDWR)
from lib.logger import logger


class Socket:

    def __init__(self) -> None:
        self.skt = socket(AF_INET, SOCK_DGRAM)
        return

    def bind(self, host, port) -> None:
        self.skt.bind((host, port))
        self.skt.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        return

    def sendto(self, data: bytearray, addr: tuple):
        return self.skt.sendto(data, addr)

    def recvfrom(self, maxlen):
        return self.skt.recvfrom(maxlen)

    def close(self):
        try:
            logger.debug("[Socket] Closing socket...")
            self.skt.shutdown(SHUT_RDWR)
            self.skt.close()
            logger.debug("[Socket] Socket closed.")
        except OSError:
            return

    def __del__(self):
        """
        Destructor for releasing resources in case something goes wrong.
        Wrapper around close(2).
        """
        self.close()
