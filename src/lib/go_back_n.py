from collections import deque

# Lib
from lib.rdt_interface import RDTInterface, RecvCallback, SendCallback
from lib.rtt_handler import RTTHandler


class GoBackN(RDTInterface):

    def __init__(self, _send: SendCallback, _recv: RecvCallback,
                 window_size: int = 10) -> None:
        self.n = window_size
        self._send_datagram = _send
        self._recv_datagram = _recv
        self.base = 0
        self.next = 0
        self.sn_send = 0
        self.sn_recv = 0
        self.rtt = RTTHandler()
        return

    def send(self, data: bytearray):
        base = 0

        while base < len(data):
            _send_window(base, )

        return

    def recv(self, length):
        pass
