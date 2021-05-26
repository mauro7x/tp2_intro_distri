from threading import Thread

# Lib
from lib.socket_udp import Socket
from lib.client_handler import ClientHandler
from lib.logger import logger
from lib.rdt_interface import sendto_fixed_addr, MAX_DATAGRAM_SIZE
from lib.stats import stats


class Receiver:

    def __init__(self, skt: Socket):
        self.th = Thread(None, self._run)
        self.skt = skt
        self.receiving = True
        self.clients: dict[tuple[str, int], ClientHandler] = {}
        self.th.start()

    def _demux(self, addr, data):
        if addr not in self.clients:
            self.clients[addr] = ClientHandler(
                sendto_fixed_addr(self.skt, addr), addr)
            logger.debug(
                f"{addr[0]}:{addr[1]} request assigned to ClientHandler:"
                f"{self.clients[addr].id}.")
            stats['requests']['total'] += 1

        self.clients[addr].push(data)

    def _run(self):
        while self.receiving:
            data, addr = self.skt.recvfrom(MAX_DATAGRAM_SIZE)

            if not addr:
                logger.debug("[Receiver] Stopped.")
                break

            self._demux(addr, data)
            self._join_handlers()

        logger.debug("[Receiver] Joining handlers...")
        self._join_handlers(True)

    def _join_handlers(self, force=False):
        active_handlers = {}

        for addr, handler in self.clients.items():
            if force or handler.is_done():
                handler.join(force)
                continue
            active_handlers[addr] = handler

        self.clients = active_handlers

    def stop(self):
        logger.debug('[Receiver] Stopping...')
        self.receiving = False
        self.skt.close()
        self.th.join()
        logger.debug('[Receiver] Joined.')
