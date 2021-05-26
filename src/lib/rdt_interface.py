from abc import abstractmethod
from typing import Callable, Optional

from lib.socket_udp import Socket


RecvCallback = Callable[[int, Optional[int], Optional[int]], bytearray]
SendCallback = Callable[[bytearray], int]


def sendto_fixed_addr(skt: Socket, addr: tuple):
    def send(data: bytearray):
        return skt.sendto(data, addr)

    return send


def recvfrom_fixed_addr(skt: Socket):
    def recv(length: int):
        return skt.recvfrom(length)[0]
    return recv


class RDTInterface:

    @abstractmethod
    def send(self, data):
        pass

    @abstractmethod
    def recv(self, length, timeout):
        pass
