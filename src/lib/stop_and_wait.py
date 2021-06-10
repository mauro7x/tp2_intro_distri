from time import perf_counter as now

# Lib
from lib.rdt_interface import (ACK_TYPE, DATA_TYPE,
                               MAX_PAYLOAD_SIZE, MAX_LAST_TIMEOUTS,
                               RDTInterface, RecvCallback, SendCallback, split)
from lib.logger import logger
from lib.rtt_handler import RTTHandler
from lib.socket_udp import SocketTimeout


# Aux private funcs


def _get_next(value):
    """
    TODO: docs.
    """

    if value == b'0':
        return b'1'
    return b'0'


def _get_prev(value):
    """
    TODO: docs.
    """

    return _get_next(value)


class StopAndWait(RDTInterface):
    """
    TODO: docs.
    """

    def __init__(self, send: SendCallback, recv: RecvCallback) -> None:
        self._send_datagram = send
        self._recv_datagram = recv
        self.sn_send = b'0'
        self.sn_recv = b'0'
        self.stopped = False
        self.rtt = RTTHandler()
        return

    def send(self, data: bytearray, last=False):
        """
        TODO: docs.
        """
        logger.debug('[s&w:send] == START SENDING ==')
        logger.debug(f'[s&w:send] Data to send: {data[:10]} - '
                     f'len {len(data)} -')

        for i in range(0, len(data), MAX_PAYLOAD_SIZE):
            # We divide total data in segments of max size MAX_PAYLOAD_SIZE
            payload = data[i:(i + MAX_PAYLOAD_SIZE)]
            datagram = DATA_TYPE + self.sn_send + payload

            # We send the datagram
            logger.debug(f'[s&w:send] Sending datagram ({datagram[:10]} - '
                         f'len {len(datagram)})...')
            self._send_datagram(datagram)
            start = now()
            timeouts = 0
            datagram_ackd = False

            while not datagram_ackd:
                try:
                    # We block receiving a datagram...
                    datagram_recd = self._recv_datagram(
                        self.rtt.get_timeout(), start)
                    type, sn, _ = split(datagram_recd)
                except SocketTimeout:
                    if last and i + MAX_PAYLOAD_SIZE >= len(data) and\
                            ((timeouts := timeouts + 1) >= MAX_LAST_TIMEOUTS):
                        # MAX_LAST_TIMEOUTS reached and we are sending
                        # last piece of data, we assume data arrived
                        # but its ack was lost.
                        logger.warn('Client request assumed to have been '
                                    'fulfilled (timeouts limit has been '
                                    'reached while waiting for ACK).')
                        break

                    # Time out! We re-send the datagram
                    logger.debug(
                        '[s&w:send] Timed out. Re-sending datagram '
                        f'{datagram[:10]} - len {len(datagram)} -')
                    self.rtt.timed_out()
                    self._send_datagram(datagram)
                    start = now()
                    continue

                # Datagram has arrived
                if type == DATA_TYPE:
                    # Datagram is data type, so we re-send last sn_recv.
                    logger.debug('[s&w:send] DATA received. Re-sending'
                                 ' last ACK with sn_recv.')
                    self._send_datagram(
                        ACK_TYPE + _get_prev(self.sn_recv))
                    continue

                # Datagram is ACK type, we check if it matches our sn_send.
                if (datagram_ackd := (sn == self.sn_send)):
                    self.rtt.add_sample(now() - start)
                    logger.debug(
                        f'[s&w:send] Good ACK received. (current timeout: '
                        f'{self.rtt.get_timeout()*1000} ms)')
                else:
                    logger.debug(f'[s&w:send] Wrong ACK received ({sn}, '
                                 f'expected {self.sn_send}).')

            self.sn_send = _get_next(self.sn_send)

        logger.debug('[s&w:send] == FINISH SENDING ==')
        return

    def recv(self, length):
        """
        TODO: docs.
        """
        logger.debug('[s&w:recv] == START RECEIVING ==')
        logger.debug(f'[s&w:recv] Length: {length}')

        # TODO: Add global timer so it doesn't block 4ever?

        result = []
        total_recd = 0

        while total_recd < length:
            type, sn, data = split(self._recv_datagram())

            if type == ACK_TYPE:
                logger.debug('[s&w:recv] ACK arrived, we expected DATA.')
                continue

            # If seq numbers dont't match we re-send the last ack
            if sn != self.sn_recv:
                logger.debug(
                    f'[s&w:recv] Wrong SN received ({sn}, '
                    f'expected {self.sn_recv}). Re-sending '
                    f'last ackd SN ({self.sn_recv})...')
                self._send_datagram(ACK_TYPE + _get_prev(self.sn_recv))
                continue

            # If seq numbers match, we keep the data and continue
            logger.debug(
                f'[s&w:recv] Good SN received. Data received: {data[:10]} - '
                f'len {len(data)} -')
            result.append(data)
            total_recd += len(data)

            logger.debug(
                f'[s&w:recv] Sending ack ({self.sn_recv})...')
            self._send_datagram(ACK_TYPE + self.sn_recv)
            self.sn_recv = _get_next(self.sn_recv)

        result = b''.join(result)

        logger.debug(f'[s&w:recv] Total data received: {result[:10]} '
                     f'- len {len(data)} -')
        logger.debug('[s&w:recv] == FINISH RECEIVING ==')

        return result
