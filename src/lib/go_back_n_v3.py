from time import perf_counter as now
from math import isclose
from collections import deque, namedtuple
from heapq import heapify, heappop, heappush
from typing import Iterable

# Lib
from lib.rdt_interface import (ACK_TYPE, MAX_LAST_TIMEOUTS, split)
from lib.go_back_n_v2 import GoBackNV2
from lib.go_back_n_base import encode_sn, decode_sn
from lib.logger import logger
from lib.socket_udp import SocketTimeout

DatagramTime = namedtuple('DatagramTime', ['start', 'pn'])


def _is_expired(time: float, timeout: float):
    return (time <= now() - timeout or
            isclose(time, now() - timeout, rel_tol=0.01))


class Timers:

    def __init__(self):
        self.heap: 'list[DatagramTime]' = []
        return

    def add_timer(self, start: int, i: int) -> None:
        logger.debug(f'Adding timer for pn: {i}')
        heappush(self.heap, DatagramTime(start, i))

    def get_expired(self, timeout: float) -> set:
        expired = set()
        while self.heap and _is_expired(self.heap[0].start, timeout):
            dt = heappop(self.heap)
            logger.debug(f"Time expired for: {dt.pn}")
            expired.add(dt.pn)
        return expired

    def get_min_start_time(self) -> float:
        return self.heap[0].start

    def remove_ackd(self, ackd_pns: Iterable):
        for pn in ackd_pns:
            try:
                self.heap.remove(pn)
            except ValueError:
                pass
        heapify(self.heap)
        return


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

            while send_queue:
                pn = send_queue.pop()
                self._send_datagram(datagrams[pn])
                timers.add_timer(now(), pn)

            while base < len(datagrams):
                try:
                    start_time = timers.get_min_start_time()
                    datagram_recd = self._recv_datagram(
                        self.rtt.get_timeout(), start_time)
                    type, sn, data = split(datagram_recd)
                    sn = decode_sn(sn)
                except SocketTimeout:
                    expired = timers.get_expired(self.rtt.get_timeout())
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
                timers.remove_ackd(ackd_pns)

                self.rtt.add_samples(now() - start_time, pn - base)
                timeouts = 0
                new_count = pn - base + 1
                wnd_end = min(base + self.n, len(datagrams))
                logger.debug(
                    '[gbn:send] Adding data to send-queue:'
                    f' {base + self.n - new_count} to {wnd_end}'
                    f'[{self._get_sn(base)}, {self._get_sn(wnd_end)}]')
                # Add new datagrams
                send_queue |= {i for i in range(
                    base + self.n - new_count, wnd_end)}

                base = pn + 1
                self._calc_transform(base)
                break

        self.sn_send = self._get_sn(base)

        logger.debug('[gbn:send] == FINISH SENDING ==')
        return
