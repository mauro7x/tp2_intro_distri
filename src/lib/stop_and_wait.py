from time import monotonic as now

# Lib
from lib.rdt_common import DATAGRAM_SIZE, recv_datagram, send_datagram
from lib.rdt_interface import RDTInterface, RecvCallback, SendCallback
from lib.logger import logger
from lib.socket_udp import SocketTimeout

# Sizes
ACK_SIZE = len(b'0')
assert DATAGRAM_SIZE > ACK_SIZE
DATA_SIZE = DATAGRAM_SIZE - ACK_SIZE

# Timeouts
TIMEOUT = 2  # in seconds
DISCONNECT_TIMEOUT = 5  # in seconds


# Aux private funcs

def _split(datagram):
    """
    TODO: docs.
    """

    return datagram[:ACK_SIZE], datagram[ACK_SIZE:]


class StopAndWait(RDTInterface):
    """
    TODO: docs.
    """

    def __init__(self, send: SendCallback, recv: RecvCallback) -> None:
        self._send = send
        self._recv = recv
        self.seq_num = b'0'
        self.seq_ack = b'0'
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

    def send(self, total_data: bytearray):
        """
        TODO: docs.
        """

        logger.debug(f'[saw:send] == START SENDING ==')
        logger.debug(f'[saw:send] Data to send: {total_data}')

        for i in range(0, len(total_data), DATA_SIZE):
            # We divide total data in segments of DATA_SIZE
            data = total_data[i:(i + DATA_SIZE)]
            datagram = self.seq_num + data

            logger.debug(f'[saw:send] Sending datagram ({datagram})...')
            send_datagram(datagram, self._send)
            start = now()

            datagram_ackd = False
            while not datagram_ackd:
                try:
                    # We wait for the ack to arrive
                    ack, _ = _split(recv_datagram(self._recv, TIMEOUT, start))
                    datagram_ackd = (ack == self.seq_num)
                    if datagram_ackd:
                        logger.debug(
                            f'[saw:send] Good ACK received.')
                    else:
                        logger.debug(
                            f'[saw:send] Wrong ACK received ({ack}, expected {self.seq_num}).')

                except SocketTimeout:
                    # If recv timed out, we re-send the chunk
                    logger.debug(
                        f'[saw:send] Timed out. Re-sending datagram ({datagram})...')
                    send_datagram(datagram, self._send)
                    start = now()

            self.seq_num = self._get_next(self.seq_num)

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
            sn, data = _split(recv_datagram(self._recv))

            # If acks dont't match we re-send the last ack
            if sn != self.seq_ack:
                logger.debug(
                    f'[saw:recv] Wrong SN received ({sn}). Re-sending last ackd SN ({self.seq_ack})...')
                send_datagram(self._get_prev(self.seq_ack), self._send)
                continue

            # If acks match, we keep the data and continue
            logger.debug(
                f'[saw:recv] Good SN received. Data received: ({data})')
            left = length - total_recd
            result.append(data[:left])
            total_recd += len(data)

            logger.debug(
                f'[saw:recv] Sending ack ({self.seq_ack})...')
            send_datagram(self.seq_ack, self._send)
            self.seq_ack = self._get_next(self.seq_ack)

        result = b''.join(result)

        logger.debug(f'[saw:recv] Total data received: {result}')
        logger.debug(f'[saw:recv] == FINISH RECEIVING ==')

        return result
