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
        Sends the data through the UDP socket.
        Wrapper around sendto(2).

        Parameters:
        data(bytearray): datagram to be send.
        addr(tuple): destination address.

        Returns:
        Number of bytes sent.
        """

        sent = self.skt.sendto(data, addr)
        stats['bytes']['sent'] += sent
        return sent

    def recvfrom(self, maxlen: int, timeout: float = None,
                 start_time: float = 0) -> bytearray:
        """
        Receives data through the UDP socket with timeout.
        Wrapper around recvfrom(2).

        Parameters:
        maxlen(int): datagram to be send.
        timeout(float): time to block on recv.
        start_time(float): start point for the timeout.

        Returns:
        Data received.
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
