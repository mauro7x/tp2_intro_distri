from abc import abstractmethod
from os import getenv
from typing import Callable, Optional

# Lib
from lib.socket_udp import Socket

# Typing


class RecvCallback(Callable):
    def __call__(self, timeout: Optional[float],
                 start_time: Optional[float]) -> bytearray: ...


class SendCallback(Callable):
    def __call__(self, data: bytearray) -> int: ...


# Types
ACK_TYPE = b'a'
DATA_TYPE = b'd'

# Sizes
TYPE_SIZE = 1
SN_SIZE = 1
# Máx datagram size set by UDP is 65507 (2**16 - headers)
MAX_DATAGRAM_SIZE = min(getenv("MAX_DATAGRAM_SIZE", 2**14), 65507)
MAX_PAYLOAD_SIZE = MAX_DATAGRAM_SIZE - (TYPE_SIZE + SN_SIZE)
assert MAX_PAYLOAD_SIZE > 0, "Invalid datagram size, must be smaller"

# Timeouts
TIMEOUT = 1  # secs (recommended start timeout by RFC 6298)
MAX_DISCONNECT_TIME = 30  # secs
MAX_LAST_TIMEOUTS = 10
DISCONNECT_TIMEOUTS = 50


def split(datagram: bytearray) -> 'tuple[bytearray, bytearray, bytearray]':
    """
    Splits the datagram according to the RDT protocol.
    """

    type = datagram[:TYPE_SIZE]
    ack = datagram[TYPE_SIZE:TYPE_SIZE + SN_SIZE]
    payload = datagram[TYPE_SIZE + SN_SIZE:]

    return type, ack, payload


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
