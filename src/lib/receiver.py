from threading import Thread
from time import perf_counter as now

# Lib
from lib.socket_udp import Socket, SocketTimeout
from lib.client_handler import ClientHandler
from lib.logger import logger
from lib.rdt_interface import sendto_fixed_addr, MAX_DATAGRAM_SIZE
from lib.stats import stats


MAX_TIME_BLACKLIST = 60
NEW_CONNECTION_MAX_WAIT = 1


class Receiver:

    def __init__(self, skt: Socket):
        self.th = Thread(target=self._run, name='Receiver')
        self.skt = skt
        self.receiving = True
        self.clients: dict[tuple[str, int], ClientHandler] = {}
        self.tmp_blacklist = {}
        self.th.start()

    def _demux(self, addr, data):
        """
        TODO: docs
        """
        if addr not in self.clients:
            self.clients[addr] = ClientHandler(
                sendto_fixed_addr(self.skt, addr), addr)
            logger.debug(
                f"[Receiver] {addr[0]}:{addr[1]} request assigned to "
                f"ClientHandler:{self.clients[addr].id}.")
            stats['requests']['total'] += 1

        self.clients[addr].push(data)
        return

    def _run(self):
        try:
            while self.receiving:
                try:
                    data, addr = self.skt.recvfrom(
                        MAX_DATAGRAM_SIZE, NEW_CONNECTION_MAX_WAIT, now())

                    if addr in self.tmp_blacklist and\
                            self._check_blacklist_time(addr):
                        continue

                    if not addr:
                        logger.debug("[Receiver] Stopped.")
                        break

                    self._demux(addr, data)
                except SocketTimeout:
                    pass

                self._join_handlers()

            logger.debug("[Receiver] Joining handlers...")
            self._join_handlers(True)
        except BaseException:
            logger.exception("Unexpected error during execution:")
        return

    def _check_blacklist_time(self, addr):
        if now() - self.tmp_blacklist[addr] <= MAX_TIME_BLACKLIST:
            return True
        self.tmp_blacklist.pop(addr)
        return False

    def _join_handlers(self, force=False):
        active_handlers = {}

        for addr, handler in self.clients.items():
            if force or handler.is_done():
                self.tmp_blacklist[addr] = now()
                handler.join(force)
                continue
            active_handlers[addr] = handler

        self.clients = active_handlers

    def stop(self, force=False):
        logger.debug('[Receiver] Stopping...')
        if not force and len(self.clients) > 0:
            raise RuntimeWarning("Some Handlers havent finished yet.")
        self.receiving = False
        self.skt.close()
        self.th.join()
        logger.debug('[Receiver] Joined.')
