from time import monotonic as now

# Lib
from lib.rdt_interface import (
    ACK_TYPE, DATA_TYPE, MAX_LAST_TIMEOUTS, MAX_PAYLOAD_SIZE,
    RDTInterface, RecvCallback, SN_SIZE, SendCallback, split)
from lib.rtt_handler import RTTHandler
from lib.logger import logger
from lib.socket_udp import SocketTimeout


def _encode_sn(sn: int) -> bytearray:
    return sn.to_bytes(SN_SIZE, "big")


def _decode_sn(sn: bytearray) -> int:
    return int.from_bytes(sn, "big")


class GoBackN(RDTInterface):

    def __init__(self, _send: SendCallback, _recv: RecvCallback,
                 window_size: int = 2) -> None:
        assert window_size <= (2**(8 * SN_SIZE))//2
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
        return [DATA_TYPE + _encode_sn(self._get_sn(int(i/MAX_PAYLOAD_SIZE))) +
                data[i:i+MAX_PAYLOAD_SIZE]
                for i in range(0, len(data), MAX_PAYLOAD_SIZE)]

    def _get_sn(self, pn):
        return (pn + self.sn_send) % (2 * self.n)

    def _get_prev(self, sn):
        return (sn - 1) % (2 * self.n)

    def _get_next(self, sn):
        return (sn + 1) % (2 * self.n)

    def _calc_transform(self, base):
        first_pn = (base - self.n) if (base - self.n) >= 0 else 0
        last_pn = base + self.n
        self.dict_transform = {(i + self.sn_send) % (2*self.n): i
                               for i in range(first_pn, last_pn)}
        # logger.debug("TRANSFORMATION IS: \n")
        # for i, j in self.dict_transform.items():
        #     print(i, '-->', j
        return

    def _get_pn(self, sn):
        # Funciona sin desfase, se puede buscar otra forma
        # pn = sn + ((base + self.n - 1 - sn) // (2 * self.n))\
        #     * (2 * self.n)
        return self.dict_transform[sn]

    def send(self, data: bytearray, last=False):
        logger.debug('[gbn:send] == START SENDING ==')
        logger.debug(f'[gbn:send] Data to send: {data[:10]} - '
                     f'len {len(data)} -')

        #    base      window_end
        # -- |------> n| ---
        # 01 |234567...
        timeouts = 0

        base = 0
        self._calc_transform(base)
        datagrams = self._create_datagrams(data)

        logger.debug(f'[gbn:send] Datagram count: {len(datagrams)}')

        while base < len(datagrams):

            start = now()
            wnd_end = min(base + self.n, len(datagrams))
            logger.debug(
                f'[gbn:send] Sending from {base} to'
                f' {wnd_end} with sns: '
                f'[{self._get_sn(base)}, {self._get_sn(wnd_end)}]')
            for i in range(base, wnd_end):
                self._send_datagram(datagrams[i])

            while base < len(datagrams):
                try:
                    datagram_recd = self._recv_datagram(
                        self.rtt.get_timeout(), start)
                    type, sn, data = split(datagram_recd)
                    sn = _decode_sn(sn)
                except SocketTimeout:
                    if last and timeouts >= MAX_LAST_TIMEOUTS:
                        # Assume everything was sent
                        base = len(datagrams) + 1
                    logger.debug('[gbn:send] Timed out. Resending...')
                    break

                if type != ACK_TYPE:
                    datagram = ACK_TYPE + \
                        _encode_sn(self._get_prev(self.sn_recv))
                    self._send_datagram(datagram)
                    continue

                # got ack
                logger.debug(f'[gbn:send] Got ack sn: {sn}')
                pn = self._get_pn(sn)

                if pn < base:
                    continue

                # enviamos lo nuevo
                start = now()
                new_count = pn - base + 1
                wnd_end = min(base + self.n, len(datagrams))
                logger.debug(
                    f'[gbn:send] Sending new data {base + self.n - new_count} '
                    f'to {wnd_end}'
                    f'[{self._get_sn(base)}, {self._get_sn(wnd_end)}]')
                for i in range(base + self.n - new_count, wnd_end):
                    self._send_datagram(datagrams[i])

                base = pn + 1
                self._calc_transform(base)

        self.sn_send = self._get_sn(base)

        logger.debug('[gbn:send] == FINISH SENDING ==')
        return

    def recv(self, length):
        logger.debug('[gbn:recv] == START RECEIVING ==')
        logger.debug(f'[gbn:recv] Length: {length}')

        # TODO: Add global timer so it doesn't block 4ever?

        result = []
        total_recd = 0

        while total_recd < length:
            type, sn, data = split(self._recv_datagram())
            sn = _decode_sn(sn)

            if type == ACK_TYPE:
                logger.debug('[gbn:recv] ACK arrived, we expected DATA.')
                continue

            # If seq numbers dont't match we re-send the last ack
            if sn != self.sn_recv:
                logger.debug(
                    f'[gbn:recv] Wrong SN received ({sn}, '
                    f'expected {self.sn_recv}). Re-sending '
                    f'last ackd SN ({self.sn_recv})...')
                self._send_datagram(
                    ACK_TYPE + _encode_sn(self._get_prev(self.sn_recv)))
                continue

            # If seq numbers match, we keep the data and continue
            logger.debug(
                f'[gbn:recv] Good SN received. Data received: {data[:10]} - '
                f'len {len(data)} -')
            result.append(data)
            total_recd += len(data)

            logger.debug(
                f'[gbn:recv] Sending ack ({self.sn_recv})...')
            self._send_datagram(ACK_TYPE + _encode_sn(self.sn_recv))
            self.sn_recv = self._get_next(self.sn_recv)

        result = b''.join(result)

        logger.debug(f'[gbn:recv] Total data received: {result[:10]} '
                     f'- len {len(data)} -')
        logger.debug('[gbn:recv] == FINISH RECEIVING ==')

        return result
