from lib.rdt_interface import RDTInterface
from lib.logger import logger


class StopAndWait(RDTInterface):

    def __init__(self, send, recv) -> None:
        self._send = send
        self._recv = recv
        return

    def send(self, data):
        logger.debug(f"Sending data: {data}")
        return self._send(data)

    def recv(self, length):
        return self._recv(length)
