from time import monotonic as now

# Lib
from lib.rdt_interface import (
    TYPE_SIZE, ACK_TYPE, DATA_TYPE, SN_SIZE, MAX_PAYLOAD_SIZE, TIMEOUT, RDTInterface, RecvCallback, SendCallback)
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

    def _get_next(self, value):
        """
        TODO: docs.
        """

        if value == b'0':
            return b'1'
        else:
            return b'0'

    def _get_prev(self, value):
        """
        TODO: docs.
        """

        return self._get_next(value)

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

            logger.debug(f'[saw:send] Sending datagram ({datagram})...')
            self._send_datagram(datagram)
            start = now()
            timeouts = 0

            datagram_ackd = False
            while (not datagram_ackd) and (timeouts < 100):
                try:
                    # We wait for the ack to arrive
                    type, sn, _ = _split(self._recv_datagram(TIMEOUT, start))

                    if type == DATA_TYPE:
                        self._send_datagram(
                            ACK_TYPE + self._get_prev(self.sn_recv))
                        continue

                    datagram_ackd = (sn == self.sn_send)

                    if datagram_ackd:
                        logger.debug(
                            f'[saw:send] Good ACK received.')
                    else:
                        logger.debug(
                            f'[saw:send] Wrong ACK received ({sn}, expected {self.sn_send}).')

                except SocketTimeout:
                    # If recv timed out, we re-send the chunk
                    timeouts += 1
                    logger.debug(
                        f'[saw:send] Timed out. Re-sending datagram ({datagram})...')
                    self._send_datagram(datagram)
                    start = now()

            if timeouts == 100:
                # TODO: identificar si estamos en el ultimo paquete
                raise SocketTimeout()

            self.sn_send = self._get_next(self.sn_send)

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
                self._send_datagram(ACK_TYPE + self._get_prev(self.sn_recv))
                continue

            # If seq numbers match, we keep the data and continue
            logger.debug(
                f'[saw:recv] Good SN received. Data received: ({data})')
            result.append(data)
            total_recd += len(data)

            logger.debug(
                f'[saw:recv] Sending ack ({self.sn_recv})...')
            self._send_datagram(ACK_TYPE + self.sn_recv)
            self.sn_recv = self._get_next(self.sn_recv)

        result = b''.join(result)

        logger.debug(f'[saw:recv] Total data received: {result}')
        logger.debug(f'[saw:recv] == FINISH RECEIVING ==')

        return result
