from time import monotonic as now
from lib.rdt_interface import RDTInterface, RecvCallback, SendCallback
from lib.logger import logger
from signal import signal, alarm, SIGALRM

ACK_SIZE = len(b'0')

TIMEOUT = 0.2  # in seconds
DISCONNECT_TIMEOUT = 5  # in seconds


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
        self.current = b'0'
        return

    def _change_current(self):
        if self.current == b'0':
            self.current = b'1'
        else:
            self.current = b'0'

    def send(self, data: bytearray):
        logger.debug(f"Sending data: {data}")

        data = (f'{self.current}').encode() + data
        start = now()
        self._send(data)

        ack = False
        while not ack:
            recd = self._recv(ACK_SIZE, timeout=TIMEOUT, start_time=start)

        return self._send(data)

    def recv(self, length):
        return self._recv(length)
