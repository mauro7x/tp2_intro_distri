from time import perf_counter as now

# Lib
from lib.rdt_interface import (ACK_TYPE, MAX_LAST_TIMEOUTS, split)
from lib.go_back_n_base import GoBackNBase, encode_sn, decode_sn
from lib.logger import logger
from lib.socket_udp import SocketTimeout


class GoBackNV1(GoBackNBase):

    def send(self, data: bytearray, last=False):
        logger.debug('[gbn:send] == START SENDING ==')
        logger.debug(f'[gbn:send] Data to send: {data[:10]} - '
                     f'len {len(data)} -')

        timeouts = 0
        base = 0
        self._calc_transform(base)
        datagrams = self._create_datagrams(data)

        prev_base = 0
        doubled_acks = 0

        logger.debug(f'[gbn:send] Datagram count: {len(datagrams)}')

        while base < len(datagrams):

            start = now()
            wnd_end = min(base + self.n, len(datagrams))
            wnd_start = min(base, wnd_end)
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
                    print(f"TIMEDOUT WITH: {self.rtt.get_timeout()}")
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

                if pn == base - 1 and prev_base == base and\
                        (doubled_acks := doubled_acks + 1) == 3:
                    doubled_acks = 0
                    break

                if pn < base:
                    continue

                prev_base = base
                doubled_acks = 0

                self.rtt.add_sample(now() - start)

                # We send new packages
                timeouts = 0
                start = now()
                new_count = pn - base + 1
                wnd_end = min(base + new_count + self.n, len(datagrams))
                wnd_start = min(base + self.n, wnd_end)
                logger.debug(
                    f'[gbn:send] Sending new data {wnd_start} '
                    f'to {wnd_end}'
                    f'[{self._get_sn(base)}, {self._get_sn(wnd_end)}]')
                for i in range(wnd_start, wnd_end):
                    self._send_datagram(datagrams[i])

                base = pn + 1
                self._calc_transform(base)

        self.sn_send = self._get_sn(base)

        logger.debug('[gbn:send] == FINISH SENDING ==')
        return

    def recv(self, length):
        logger.debug('[gbn:recv] == START RECEIVING ==')
        logger.debug(f'[gbn:recv] Length: {length}')

        # Nice to Have: Add global timer so it doesn't block forever.

        result = []
        total_recd = 0

        while total_recd < length:
            type, sn, data = split(self._recv_datagram())
            sn = decode_sn(sn)

            if type == ACK_TYPE:
                logger.debug('[gbn:recv] ACK arrived, we expected DATA.')
                continue

            # If seq numbers dont't match we re-send the last ack
            if sn != self.sn_recv:
                logger.debug(
                    f'[gbn:recv] Wrong SN received ({sn}, '
                    f'expected {self.sn_recv}). Re-sending '
                    f'last ackd SN ({self._get_prev(self.sn_recv)})...')
                self._send_datagram(
                    ACK_TYPE + encode_sn(self._get_prev(self.sn_recv)))
                continue

            # If seq numbers match, we keep the data and continue
            logger.debug(
                f'[gbn:recv] Good SN received. Data received: {data[:10]} - '
                f'len {len(data)} -')
            result.append(data)
            total_recd += len(data)

            logger.debug(
                f'[gbn:recv] Sending ack ({self.sn_recv})...')
            self._send_datagram(ACK_TYPE + encode_sn(self.sn_recv))
            self.sn_recv = self._get_next(self.sn_recv)

        result = b''.join(result)

        logger.debug(f'[gbn:recv] Total data received: {result[:10]} '
                     f'- len {len(data)} -')
        logger.debug('[gbn:recv] == FINISH RECEIVING ==')

        return result
