from abc import abstractmethod
from typing import Callable, Optional

# Lib
from lib.socket_udp import Socket

# Typing
RecvCallback = Callable[[Optional[int], Optional[int]], bytearray]
SendCallback = Callable[[bytearray], int]

# Types
ACK_TYPE = b'a'
DATA_TYPE = b'd'

# Sizes
MAX_DATAGRAM_SIZE = 2**10  # Máx value set by UDP is 2**16 - 8
TYPE_SIZE = 1
SN_SIZE = 1
MAX_PAYLOAD_SIZE = MAX_DATAGRAM_SIZE - (TYPE_SIZE + SN_SIZE)
assert MAX_PAYLOAD_SIZE > 0

# Timeouts (in seconds)
TIMEOUT = 1  # Recommended start timeout by RFC 6298


def sendto_fixed_addr(skt: Socket, addr: tuple):
    def send(data: bytearray):
        return skt.sendto(data, addr)

    return send


def recvfrom_fixed_addr(skt: Socket):
    def recv(timeout: Optional[int] = None,
             start_time: int = 0) -> bytearray:
        return skt.recvfrom(MAX_DATAGRAM_SIZE, timeout, start_time)[0]
    return recv


class RDTInterface:

    @abstractmethod
    def send(self, data):
        pass

    @abstractmethod
    def recv(self, length, timeout):
        pass
