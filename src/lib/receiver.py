from threading import Thread
from lib.socket_udp import Socket
from lib.client_handler import ClientHandler
from lib.logger import logger
from lib.rdt_interface import sendto_fixed_addr
# from lib.stats import stats

CHUNK_SIZE = 1024


class Receiver:

    def __init__(self, skt: Socket):
        self.th = Thread(None, self._run)
        self.skt = skt
        self.receiving = True
        self.clients: dict[tuple[str, int], ClientHandler] = {}
        self.th.start()

    def _demux(self, addr, data):
        if addr not in self.clients:
            logger.debug(f"New request from: {addr}")
            self.clients[addr] = ClientHandler(
                sendto_fixed_addr(self.skt, addr), addr)

        self.clients[addr].push(data)

    def _run(self):
        while self.receiving:
            data, addr = self.skt.recvfrom(CHUNK_SIZE)
            if not addr:
                logger.debug("[Receiver] Stopped.")
                break

            self._demux(addr, data)
            self._join_handlers()

        self._join_handlers(True)

    def _join_handlers(self, force=False):
        active_handlers = {}

        for addr, handler in self.clients:
            if force or handler.is_done():
                handler.join(force)
                logger.debug("[Accepter] Client joined.")
                continue
            active_handlers[addr] = handler

        self.clients = active_handlers

    def stop(self):
        self.receiving = False
        self.skt.close()
        self.th.join()
