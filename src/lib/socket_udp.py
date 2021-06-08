from socket import (SOL_SOCKET, SO_REUSEADDR, socket,
                    AF_INET, SOCK_DGRAM, SHUT_RDWR, timeout)
from time import perf_counter as now

# Lib
from lib.stats import stats

# Exceptions
SocketTimeout = timeout


class Socket:

    def __init__(self) -> None:
        """
        Inicialization of socket class.
        Wrapper around socket(2).
        """

        self.skt = socket(AF_INET, SOCK_DGRAM)
        return

    def bind(self, host, port) -> None:
        """
        Binds the socket to the received address and port number.
        Wrapper around bind(2) and setsockopt(2).

        Parameters:
        host(str): Host address.
        port(int): Port number.

        Returns:
        None.
        """

        self.skt.bind((host, port))
        self.skt.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        return

    def sendto(self, data: bytearray, addr: tuple) -> int:
        """
        TODO: docs.
        """

        sent = self.skt.sendto(data, addr)
        stats['bytes']['sent'] += sent
        return sent

    def recvfrom(self, maxlen, timeout=None, start_time: int = 0) -> bytearray:
        """
        TODO: docs.
        """

        if timeout is None:
            # Recv without timeout
            recd = self.skt.recvfrom(maxlen)
        else:
            # Recv with timeout
            try:
                self.skt.settimeout(timeout - (now() - start_time))
            except ValueError:
                raise SocketTimeout()

            recd = self.skt.recvfrom(maxlen)
            self.skt.settimeout(None)

        stats['bytes']['recd'] += len(recd[0])
        return recd

    def close(self):
        """
        Shutdowns and closes the socket, releasing resources.
        Wrapper around shutdown(2) and close(2).

        Parameters:
        None.

        Returns:
        None.
        """

        try:
            self.skt.shutdown(SHUT_RDWR)
            self.skt.close()
        except OSError:
            return

    def __del__(self):
        """
        Destructor for releasing resources in case something goes wrong.
        Wrapper around close(2).
        """

        self.close()
