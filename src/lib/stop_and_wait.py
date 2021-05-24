from time import clock_gettime
from lib.rdt_interface import RDTInterface
from lib.logger import logger
from signal import signal, alarm, SIGALRM

ACK_SIZE = len(b'0')


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

    def __init__(self, send, recv) -> None:
        self._send = send
        self._recv = recv
        self.current = b'0'
        return

    def _change_current(self):
        if self.current == b'0':
            self.current = b'1'
        else:
            self.current = b'0'

    def send(self, data):
        logger.debug(f"Sending data: {data}")

        data = (f'{self.current}').encode() + data
        start = clock_gettime()
        self._send(data)

        ack = False
        while not ack:
            recd = self._recv(ACK_SIZE, timeout=0.2, start)

        return self._send(data)

    def recv(self, length):
        return self._recv(length)
