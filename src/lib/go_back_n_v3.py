from time import perf_counter as now
from collections import namedtuple
from heapq import heapify, heappop, heappush
from typing import Iterable

# Lib
from lib.rdt_interface import (ACK_TYPE, MAX_LAST_TIMEOUTS, split)
from lib.go_back_n_v2 import GoBackNV2
from lib.go_back_n_base import encode_sn, decode_sn
from lib.logger import logger
from lib.socket_udp import SocketTimeout

DatagramTime = namedtuple('DatagramTime', ['start', 'pn'])


class Timers:

    def __init__(self):
        self.heap: 'list[DatagramTime]' = []
        return

    def add_timer(self, start: float, pn: int) -> None:
        logger.debug(f'[TEMPORARY] Adding timer for pn: {pn}')  # TEMP
        heappush(self.heap, DatagramTime(start, pn))

    def get_expired(self) -> set:
        expired = set()
        min_start_time = self.get_min_start_time()
        while self.heap and self.heap[0].start == min_start_time:
            dt = heappop(self.heap)
            logger.debug(f"[TEMPORARY] Time expired for: {dt.pn}")  # TEMP
            expired.add(dt.pn)
        return expired

    def get_min_start_time(self) -> float:
        return self.heap[0].start

    def remove_ackd(self, ackd_pns: Iterable):
        to_remove = []
        for dt in self.heap:
            if dt.pn in ackd_pns:
                to_remove.append(dt)

        sum = 0
        for dt in to_remove:
            self.heap.remove(dt)
            sum += dt.start
        heapify(self.heap)

        return sum / len(to_remove)


class GoBackNV3(GoBackNV2):

    def send(self, data: bytearray, last=False):
        logger.debug('[gbn:send] == START SENDING ==')

        timeouts = 0
        base = 0
        self._calc_transform(base)
        datagrams = self._create_datagrams(data)
        send_queue = set([i for i in range(min(self.n, len(datagrams)))])
        timers = Timers()

        logger.debug(f'[gbn:send] Data to send: {data[:10]} - '
                     f'len {len(data)} -. Datagram count: {len(datagrams)}')

        while base < len(datagrams):

            logger.debug(
                f'[gbn:send] Sending: [{send_queue}] (len {len(send_queue)})')

            start = now()
            while send_queue:
                pn = send_queue.pop()
                self._send_datagram(datagrams[pn])
                timers.add_timer(start, pn)

            while base < len(datagrams):
                try:
                    start_time = timers.get_min_start_time()
                    datagram_recd = self._recv_datagram(
                        self.rtt.get_timeout(), start_time)
                    type, sn, data = split(datagram_recd)
                    sn = decode_sn(sn)
                except SocketTimeout:
                    expired = timers.get_expired()
                    send_queue.update(expired)
                    self.rtt.timed_out()
                    timeouts += 1
                    logger.debug('[gbn:send] Timed out. Expired packets:'
                                 f' {expired}')
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
                    f'[gbn:send] Got ack sn: {sn} (pn: {pn}, base: {base})')

                if pn < base:
                    continue

                # Remove already akd datagrams
                ackd_pns = {i for i in range(base, pn + 1)}
                send_queue -= ackd_pns
                avg_start_time = timers.remove_ackd(ackd_pns)

                self.rtt.add_samples(now() - avg_start_time, pn - base)
                print(f'>>> RTT: {self.rtt.get_timeout()}')

                # We send new packages
                timeouts = 0
                new_count = pn - base + 1
                wnd_end = min(base + new_count + self.n, len(datagrams))
                logger.debug(
                    '[gbn:send] Adding data to send-queue: '
                    f'{base + self.n} to {wnd_end}')
                # Add new datagrams
                send_queue |= {i for i in range(
                    base + self.n, wnd_end)}

                base = pn + 1
                self._calc_transform(base)
                break

        self.sn_send = self._get_sn(base)

        logger.debug('[gbn:send] == FINISH SENDING ==')
        return
