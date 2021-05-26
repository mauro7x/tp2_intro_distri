from typing import Optional

# Lib
from lib.rdt_interface import RecvCallback, SendCallback

# Config
DATAGRAM_SIZE = 16


def _add_padding(data: bytearray) -> bytearray:
    """
    TODO: docs.
    """

    length = len(data)
    if length < DATAGRAM_SIZE:
        padding_size = DATAGRAM_SIZE - length
        data = data + (b'0' * padding_size)
    return data


def recv_datagram_from(recv: RecvCallback, timeout: Optional[int] = None,
                       start_time: int = 0) -> bytearray:
    """
    TODO: docs.
    """

    data, addr = recv(DATAGRAM_SIZE, timeout, start_time)
    return _add_padding(data), addr


def recv_datagram(recv: RecvCallback, timeout: Optional[int] = None,
                  start_time: int = 0) -> bytearray:
    """
    TODO: docs.
    """

    return _add_padding(recv(DATAGRAM_SIZE, timeout, start_time))


def send_datagram(datagram: bytearray, send: SendCallback) -> int:
    """
    TODO: docs.
    """
    # It's not necessary to send fixed length datagrams, because
    # receiver will add padding to make them fixed-size. This way
    # we avoid sending padding over the network.
    return send(datagram)
