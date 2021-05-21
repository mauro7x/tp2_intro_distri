from threading import Thread
from collections import deque
from lib.client_handler import ClientHandler
from lib.socket_tcp import Socket
from lib.logger import logger
from lib.stats import stats


class Accepter:

    def __init__(self, skt: Socket):
        self.th = Thread(None, self._run)
        self.skt = skt
        self.accepting = True
        self.clients = deque()
        self.th.start()

    def _run(self):
        while self.accepting:
            logger.debug("[Accepter] Waiting for client...")
            try:
                addr, peer = self.skt.accept()
            except OSError:
                break
            stats["connections"] += 1
            self.clients.append(ClientHandler(peer, addr))
            self._join_connections()
        self._join_connections(True)

    def _join_connections(self, force=False):
        for _ in range(len(self.clients)):
            handler = self.clients.popleft()

            if force or handler.is_done():
                handler.join(force)
                logger.debug("[Accepter] Client joined.")
                continue

            self.clients.append(handler)

    def stop(self):
        self.accepting = False
        self.skt.close()
        self.th.join()
