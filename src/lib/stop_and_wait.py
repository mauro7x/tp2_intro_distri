from itertools import islice
from time import monotonic as now
from lib.protocol import CHUNK_SIZE
from lib.rdt_interface import RDTInterface, RecvCallback, SendCallback
from lib.logger import logger
from signal import signal, alarm, SIGALRM

from lib.socket_udp import SocketTimeout

ACK_SIZE = len(b'0')

TIMEOUT = 2  # in seconds
DISCONNECT_TIMEOUT = 5  # in seconds

CHUNK_SIZE = 8


class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        seconds = seconds
        error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal(signal.SIGALRM, self.handle_timeout)
        alarm(self.seconds)

    def __exit__(self, type, value, traceback):
        alarm(0)


class StopAndWait(RDTInterface):

    def __init__(self, send: SendCallback, recv: RecvCallback) -> None:
        self._send = send
        self._recv = recv
        self.seq_num = b'0'
        self.seq_ack = b'0'
        self.buffer = None
        return

    def _get_next(self, value):
        if value == b'0':
            return b'1'
        else:
            return b'0'

    def _get_prev(self, value):
        return self._get_next(value)

    def send(self, data: bytearray):
        # [A, B, C, D] chunk = 2
        logger.debug(f"Sending data: {data}")

        for i in range(0, len(data), CHUNK_SIZE):
            chunk = self.seq_num + data[i*CHUNK_SIZE:(i+1)*CHUNK_SIZE]
            self._send(chunk)
            logger.debug(f'Sending chunk: {chunk}')
            start = now()

            ack = False
            while not ack:
                try:
                    recd = self._recv(
                        ACK_SIZE, timeout=TIMEOUT, start_time=start)
                    logger.debug(f'Received ack: {recd}')
                    ack = (recd[:ACK_SIZE] == self.seq_num)
                except SocketTimeout:
                    logger.debug(f'Resending chunk: {chunk}')
                    self._send(chunk)
                    start = now()
            print(f'Antes: {self.seq_num}')
            self.seq_num = self._get_next(self.seq_num)
            print(f'Despues: {self.seq_num}')
        return self._send(data)

    def recv(self, length):
        result = []
        total = 0
        logger.debug(f'Expecting: {length} bytes')

        while total < length:
            # Se bloquea infinito
            recd = self._recv(min(CHUNK_SIZE, length - total + ACK_SIZE))
            logger.debug(f'Received chunk: {recd}')
            if self.seq_ack != recd[:ACK_SIZE]:
                self._send(self._get_prev(self.seq_ack))
                logger.debug(f'Resending ack: {self._get_prev(self.seq_ack)}')
                continue
            result.append(recd[ACK_SIZE:])
            total += (len(recd) - ACK_SIZE)
            self._send(self.seq_ack)
            self.seq_ack = self._get_next(self.seq_ack)

        result = b''.join(result)
        logger.debug(f'Received: {result}')
        return result
