from time import monotonic as now
from lib.rdt_interface import RDTInterface, RecvCallback, SendCallback
from lib.logger import logger
from lib.socket_udp import SocketTimeout

# Sizes
CHUNK_SIZE = 4
ACK_SIZE = len(b'0')
MAX_PAYLOAD_SIZE = CHUNK_SIZE - ACK_SIZE

# Timeouts
TIMEOUT = 2  # in seconds
DISCONNECT_TIMEOUT = 5  # in seconds

class StopAndWait(RDTInterface):
    """
    TODO: docs.
    """

    def __init__(self, send: SendCallback, recv: RecvCallback) -> None:
        self._send = send
        self._recv = recv
        self.seq_num = b'0'
        self.seq_ack = b'0'
        self.buffer = None
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
        
        for i in range(0, len(data), MAX_PAYLOAD_SIZE):
            # We divide data in segments of MAX_PAYLOAD_SIZE
            payload = data[i:(i+MAX_PAYLOAD_SIZE)]

            # We form the chunk to send: seq_num + payload
            chunk = self.seq_num + payload

            self._send(chunk)
            start = now()

            ackd = False
            while not ackd:
                try:
                    # We wait for the ack to arrive
                    recd = self._recv(
                        ACK_SIZE, timeout=TIMEOUT, start_time=start)    
                    ackd = (recd == self.seq_num)
                except SocketTimeout:
                    # If recd timed out, we re-send the chunk
                    self._send(chunk)
                    start = now()
            
            self.seq_num = self._get_next(self.seq_num)
          
        return

    def recv(self, length):
        """
        TODO: docs.
        """
        
        # TODO: Add global timer so it doesn't block 4ever?

        result = []
        total = 0

        while total < length:
            bytes_to_recv = min(CHUNK_SIZE, length - total + ACK_SIZE)
            recd = self._recv(bytes_to_recv)

            # If acks dont't match we re-send the last ack
            if self.seq_ack != recd[:ACK_SIZE]:
                self._send(self._get_prev(self.seq_ack))
                continue

            # If acks match, we keep the data and continue
            result.append(recd[ACK_SIZE:])
            total += (len(recd) - ACK_SIZE)
            self._send(self.seq_ack)
            self.seq_ack = self._get_next(self.seq_ack)

        result = b''.join(result)
        return result
