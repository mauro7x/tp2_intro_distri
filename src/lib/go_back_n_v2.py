# Lib
from lib.rdt_interface import (ACK_TYPE, split)
from lib.go_back_n_base import encode_sn, decode_sn
from lib.go_back_n_v1 import GoBackNV1
from lib.logger import logger


class GoBackNV2(GoBackNV1):

    def _consume_buffer(self, result, buffer):
        current = self.sn_recv
        data_consumed = 0
        while True:
            data = buffer[current]
            if data is None:
                self.sn_recv = current
                break
            data_consumed += len(data)
            result.append(data)
            buffer[current] = None
            current = (current + 1) % len(buffer)

        return data_consumed

    def recv(self, length):
        logger.debug('[gbn:recv] == START RECEIVING ==')
        logger.debug(f'[gbn:recv] Length: {length}')

        # Nice to Have: Add global timer so it doesn't block forever.

        result = []
        total_recd = 0

        buffer = [None for i in range(2 * self.n)]

        while total_recd < length:
            type, sn, data = split(self._recv_datagram())
            sn = decode_sn(sn)

            if type == ACK_TYPE:
                logger.debug('[gbn:recv] ACK arrived, we expected DATA.')
                continue

            q, r = divmod(self.sn_recv + self.n, len(buffer))
            valid_sn = (0 <= sn < q*r) or (self.sn_recv <= sn <
                                           (self.sn_recv + self.n - q*r))

            # If seq numbers dont't match we re-send the last ack
            if not valid_sn:
                logger.debug(
                    f'[gbn:recv] Wrong SN received ({sn}, '
                    f'expected {self.sn_recv}). Re-sending '
                    f'last ackd SN ({self.sn_recv})...')
                self._send_datagram(
                    ACK_TYPE + encode_sn(self._get_prev(self.sn_recv)))
                continue

            buffer[sn] = data
            if sn != self.sn_recv:
                logger.debug(
                    f'[gbn:recv] Future SN received, buffering {sn} '
                    f'(expecting {self.sn_recv})')
                continue

            # sn == self.sn_recv -> We can use buffered data

            total_recd += self._consume_buffer(result, buffer)
            logger.debug(
                '[gbn:recv] Good SN received. Consumed buffer, now'
                f'expecting: {self.sn_recv}, before: {sn}')

            logger.debug(
                f'[gbn:recv] Sending ack ({self._get_prev(self.sn_recv)})...')
            self._send_datagram(
                ACK_TYPE + encode_sn(self._get_prev(self.sn_recv)))

        result = b''.join(result)

        logger.debug(f'[gbn:recv] Total data received: {result[:10]} '
                     f'- len {len(data)} -')
        logger.debug('[gbn:recv] == FINISH RECEIVING ==')

        return result
