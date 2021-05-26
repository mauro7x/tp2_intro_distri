from abc import abstractmethod
from typing import Callable, Optional

# Lib
from lib.socket_udp import Socket


RecvCallback = Callable[[int, Optional[int], Optional[int]], bytearray]
SendCallback = Callable[[bytearray], int]


def sendto_fixed_addr(skt: Socket, addr: tuple):
    def send(data: bytearray):
        return skt.sendto(data, addr)

    return send


def recvfrom_fixed_addr(skt: Socket):
    def recv(length: int, timeout: Optional[int] = None,
             start_time: int = 0) -> bytearray:
        return skt.recvfrom(length, timeout, start_time)[0]
    return recv


class RDTInterface:

    @abstractmethod
    def send(self, data):
        pass

    @abstractmethod
    def recv(self, length, timeout):
        pass
    
    @abstractmethod
    def stop(self):
        pass
