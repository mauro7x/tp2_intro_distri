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

        for i in range(0, len(total_data), DATA_SIZE):
            # We divide total data in segments of DATA_SIZE
            data = total_data[i:(i + DATA_SIZE)]
            datagram = self.seq_num + data

            send_datagram(datagram, self._send)
            start = now()

            datagram_ackd = False
            while not datagram_ackd:
                try:
                    # We wait for the ack to arrive
                    ack, _ = _split(recv_datagram(self._recv, TIMEOUT, start))
                    datagram_ackd = (ack == self.seq_num)
                except SocketTimeout:
                    # If recv timed out, we re-send the chunk
                    send_datagram(datagram, self._send)
                    start = now()

            self.seq_num = self._get_next(self.seq_num)

        return

    def recv(self, length):
        """
        TODO: docs.
        """

        # TODO: Add global timer so it doesn't block 4ever?

        result = []
        total_recd = 0

        while total_recd < length:
            ack, data = _split(recv_datagram(self._recv))

            # If acks dont't match we re-send the last ack
            if ack != self.seq_ack:
                send_datagram(self._get_prev(self.seq_ack), self._send)
                continue

            # If acks match, we keep the data and continue
            left = length - total_recd
            result.append(data[:left])
            total_recd += len(data)

            send_datagram(self.seq_ack, self._send)
            self.seq_ack = self._get_next(self.seq_ack)

        return b''.join(result)
