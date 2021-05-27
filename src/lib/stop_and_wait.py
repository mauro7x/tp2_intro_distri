from time import monotonic as now

# Lib
from lib.rdt_interface import (MAX_LAST_TIMEOUTS, TYPE_SIZE, ACK_TYPE,
                               DATA_TYPE, SN_SIZE, MAX_PAYLOAD_SIZE, TIMEOUT,
                               RDTInterface, RecvCallback, SendCallback)
from lib.logger import logger
from lib.socket_udp import SocketTimeout


# Aux private funcs
def _split(datagram):
    """
    TODO: docs.
    """

    type = datagram[:TYPE_SIZE]
    ack = datagram[TYPE_SIZE:TYPE_SIZE + SN_SIZE]
    payload = datagram[TYPE_SIZE + SN_SIZE:]

    return type, ack, payload


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
        return

    def send(self, data: bytearray):
        """
        TODO: docs.
        """

        logger.debug(f'[saw:send] == START SENDING ==')
        logger.debug(f'[saw:send] Data to send: {data}')

        for i in range(0, len(data), MAX_PAYLOAD_SIZE):
            # We divide total data in segments of max size MAX_PAYLOAD_SIZE
            payload = data[i:(i + MAX_PAYLOAD_SIZE)]
            datagram = DATA_TYPE + self.sn_send + payload

            # We send the datagram
            logger.debug(f'[saw:send] Sending datagram ({datagram})...')
            self._send_datagram(datagram)
            start = now()
            timeouts = 0
            datagram_ackd = False

            while (not datagram_ackd) and (timeouts < MAX_LAST_TIMEOUTS):
                try:
                    # We block receiving a datagram...
                    type, sn, _ = _split(self._recv_datagram(TIMEOUT, start))
                except SocketTimeout:
                    if ((timeouts := timeouts + 1) >= MAX_LAST_TIMEOUTS) and \
                            (i + MAX_PAYLOAD_SIZE) >= len(data):
                        # MAX_LAST_TIMEOUTS reached and we are sending
                        # last piece of data, we assume data arrived
                        # but its ack was lost.
                        logger.warn(f'Client request assumed to have been '
                                    f'fulfilled (timeouts limit has been '
                                    f'reached while waiting for ACK).')
                        break

                    # Time out! We re-send the datagram
                    logger.debug(
                        f'[saw:send] Timed out. Re-sending datagram '
                        f'({datagram})...')
                    self._send_datagram(datagram)
                    start = now()
                    continue

                # Datagram has arrived
                if type == DATA_TYPE:
                    # Datagram is data type, so we re-send last sn_recv.
                    logger.debug(f'[saw:send] DATA received. Re-sending'
                                 f' last ACK with sn_recv.')
                    self._send_datagram(
                        ACK_TYPE + _get_prev(self.sn_recv))
                    continue

                # Datagram is ACK type, we check if it matches our sn_send.
                if (datagram_ackd := (sn == self.sn_send)):
                    logger.debug(
                        f'[saw:send] Good ACK received.')
                else:
                    logger.debug(
                        f'[saw:send] Wrong ACK received ({sn}, '
                        f'expected {self.sn_send}).')

            # At this point, there are two options:
            # * Datagram successfully sent,
            # * If we are sendin the last piece of data, and MAX_LAST_TIMEOUTS
            #   is reached, we assume data arrived but ack got lost.

            self.sn_send = _get_next(self.sn_send)

        logger.debug(f'[saw:send] == FINISH SENDING ==')
        return

    def recv(self, length):
        """
        TODO: docs.
        """

        logger.debug(f'[saw:recv] == START RECEIVING ==')
        logger.debug(f'[saw:recv] Length: {length}')

        # TODO: Add global timer so it doesn't block 4ever?

        result = []
        total_recd = 0

        while total_recd < length:
            type, sn, data = _split(self._recv_datagram())

            if type == ACK_TYPE:
                logger.debug(f'[saw:recv] ACK arrived, we expected DATA.')
                continue

            # If seq numbers dont't match we re-send the last ack
            if sn != self.sn_recv:
                logger.debug(
                    f'[saw:recv] Wrong SN received ({sn}, expected {self.sn_recv}). Re-sending last ackd SN ({self.sn_recv})...')
                self._send_datagram(ACK_TYPE + _get_prev(self.sn_recv))
                continue

            # If seq numbers match, we keep the data and continue
            logger.debug(
                f'[saw:recv] Good SN received. Data received: ({data})')
            result.append(data)
            total_recd += len(data)

            logger.debug(
                f'[saw:recv] Sending ack ({self.sn_recv})...')
            self._send_datagram(ACK_TYPE + self.sn_recv)
            self.sn_recv = _get_next(self.sn_recv)

        result = b''.join(result)

        logger.debug(f'[saw:recv] Total data received: {result}')
        logger.debug(f'[saw:recv] == FINISH RECEIVING ==')

        return result
