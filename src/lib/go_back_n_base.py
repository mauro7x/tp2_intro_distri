# Lib
from lib.rdt_interface import (
    DATA_TYPE, MAX_PAYLOAD_SIZE, RDTInterface,
    RecvCallback, SN_SIZE, SendCallback)
from lib.rtt_handler import RTTHandler


def encode_sn(sn: int) -> bytearray:
    return sn.to_bytes(SN_SIZE, "big")


def decode_sn(sn: bytearray) -> int:
    return int.from_bytes(sn, "big")


class GoBackNBase(RDTInterface):
    """
    GBN protocol abstract class.
    """

    def __init__(self, _send: SendCallback, _recv: RecvCallback,
                 window_size: int = 10) -> None:
        assert window_size <= (2**(8 * SN_SIZE))//2, "Window size is too large"
        self.n = window_size
        self._send_datagram = _send
        self._recv_datagram = _recv
        self.dict_transform = {}
        self.sn_send = 0
        self.sn_recv = 0
        self.rtt = RTTHandler()
        return

    def _create_datagrams(self, data: bytearray) -> 'list[bytearray]':
        # [DATA, SN, payload]
        return [DATA_TYPE + encode_sn(self._get_sn(int(i/MAX_PAYLOAD_SIZE))) +
                data[i:i+MAX_PAYLOAD_SIZE]
                for i in range(0, len(data), MAX_PAYLOAD_SIZE)]

    def _get_prev(self, sn):
        return (sn - 1) % (2 * self.n)

    def _get_next(self, sn):
        return (sn + 1) % (2 * self.n)

    def _calc_transform(self, base):
        first_pn = (base - self.n)
        last_pn = base + self.n
        self.dict_transform = {(i + self.sn_send) % (2*self.n): i
                               for i in range(first_pn, last_pn)}
        return

    def _get_sn(self, pn):
        return (pn + self.sn_send) % (2 * self.n)

    def _get_pn(self, sn):
        return self.dict_transform[sn]

    def send(self, data: bytearray, last=False):
        assert False, "Must be implemented!"

    def recv(self, length):
        assert False, "Must be implemented!"
