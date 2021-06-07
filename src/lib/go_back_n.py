from time import monotonic as now

# Lib
from lib.rdt_interface import (
    ACK_TYPE, DATA_TYPE, MAX_LAST_TIMEOUTS, MAX_PAYLOAD_SIZE, RDTInterface, RecvCallback,
    SN_SIZE, SendCallback, _split)
from lib.rtt_handler import RTTHandler
from lib.logger import logger
from lib.socket_udp import SocketTimeout


def _encode_seqnum(sn: int) -> bytearray:
    return sn.to_bytes(SN_SIZE, "big")


class GoBackN(RDTInterface):

    def __init__(self, _send: SendCallback, _recv: RecvCallback,
                 window_size: int = 10) -> None:
        assert window_size <= (2**(8 * SN_SIZE))//2
        self.n = window_size
        self._send_datagram = _send
        self._recv_datagram = _recv
        self.sn_send = 0
        self.rtt = RTTHandler()
        return

    def _create_datagrams(self, data: bytearray) -> list[bytearray]:
        # [DATA, SN, payload]
        return [DATA_TYPE + _encode_seqnum(self._get_sn(i)) +
                data[i:i+MAX_PAYLOAD_SIZE]
                for i in range(0, len(data), MAX_PAYLOAD_SIZE)]

    def _get_sn(self, pn):
        return (pn + self.sn_send) % (2 * self.n)

    def _get_prev(self, sn):
        return (sn - 1) % (2 * self.n)

    def _calc_transform(self, base):
        first_pn = (base - self.n if (base - self.n) > 0 else base)
        last_pn = base + self.n
        self.dict_transform = {(i + self.sn_send) % (2*self.n): i
                               for i in range(first_pn, last_pn)}

    def _get_pn(self, sn):
        # Funciona sin desfase, se puede buscar otra forma
        # pn = sn + ((base + self.n - 1 - sn) // (2 * self.n))\
        #     * (2 * self.n)
        return self.dict_transform[sn]

    def send(self, data: bytearray, last=False):

        #    base      window_end
        # -- |------> n| ---
        # 01 |234567...
        timeouts = 0

        base = 0
        self._calc_transform(base)
        datagrams = self._create_datagrams(data)

        logger.debug(f'Datagrams list {datagrams}')

        while base < len(datagrams):

            start = now()
            for i in range(base, min(base + self.n, len(datagrams))):
                self._send_datagram(datagrams[i])

            while base < len(datagrams):
                try:
                    datagram_recd = self._recv_datagram(
                        self.rtt.get_timeout(), start)
                    type, sn, data = _split(datagram_recd)
                except SocketTimeout:
                    if last and timeouts >= MAX_LAST_TIMEOUTS:
                        # Assume everything was sent
                        base = len(datagrams)
                    break

                if type != ACK_TYPE:
                    datagram = ACK_TYPE + \
                        _encode_seqnum(self._get_prev(self.sn_recv))
                    self._send_datagram(datagram)
                    continue

                # got ack
                pn = self._get_pn(sn)

                if pn < base:
                    continue

                # enviamos lo nuevo
                start = now()
                new_count = pn - base + 1
                for i in range(base + self.n - new_count,
                               min(base + self.n, len(datagrams))):
                    self._send_datagram(datagrams[i])

                base = pn + 1
                self._calc_transform(base)

        self.sn_send = self._get_sn(base + 1)

        return

    def recv(self, length):
        pass
