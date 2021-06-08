from time import monotonic as now

# Lib
from lib.rdt_interface import (ACK_TYPE, MAX_LAST_TIMEOUTS, split)
from lib.go_back_n_v2 import GoBackNV2
from lib.go_back_n_base import encode_sn, decode_sn
from lib.logger import logger
from lib.socket_udp import SocketTimeout


class GoBackNV3(GoBackNV2):

    def send(self, data: bytearray, last=False):
        logger.debug('[gbn:send] == START SENDING ==')
        logger.debug(f'[gbn:send] Data to send: {data[:10]} - '
                     f'len {len(data)} -')

        timeouts = 0
        base = 0
        self._calc_transform(base)
        datagrams = self._create_datagrams(data)

        logger.debug(f'[gbn:send] Datagram count: {len(datagrams)}')

        # TODO: Add differential timers

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
                    sn = decode_sn(sn)
                except SocketTimeout:
                    self.rtt.timed_out()
                    timeouts += 1
                    logger.debug('[gbn:send] Timed out. Resending...')
                    if last and timeouts >= MAX_LAST_TIMEOUTS:
                        # Assume everything was sent
                        base = len(datagrams) + 1
                    break

                if type != ACK_TYPE:
                    datagram = ACK_TYPE + \
                        encode_sn(self._get_prev(self.sn_recv))
                    self._send_datagram(datagram)
                    continue

                # got ack
                pn = self._get_pn(sn)
                logger.debug(
                    f'[gbn:send] Got ack sn: {sn} and pn: {pn} (base: {base})')

                if pn < base:
                    continue

                self.rtt.add_sample(now() - start)
                # enviamos lo nuevo
                timeouts = 0
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
