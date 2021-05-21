from socket import (socket, AF_INET, SOCK_STREAM, SHUT_RDWR,
                    SOL_SOCKET, SO_REUSEADDR)
from lib.logger import logger
from lib.stats import stats


class Socket:

    def __init__(self, skt: socket = None) -> None:
        """
        Inicialization of socket class.
        Wrapper around socket(2).

        Parameters:
        [skt(Socket)]: Socket instance with valid fd to be copied.
        """

        logger.debug("[Socket] Creating socket...")
        if skt is None:
            self.skt = socket(AF_INET, SOCK_STREAM)
        else:
            self.skt = skt
        logger.debug("[Socket] Socket created.")

    def connect(self, host: str, port: int) -> None:
        """
        Build a connection with a especific host address and a port number.
        Wrapper around connect(2).

        Parameters:
        host: Host address.
        port(int): Port number.

        Returns:
        None.
        """
        logger.debug(f"[Socket] Connecting to {host}:{port}...")
        self.skt.connect((host, port))
        logger.debug(f"[Socket] Connected to {host}:{port}.")

    def bind(self, host: str, port: int) -> None:
        """
        Binds the socket to the received address and port number.
        Wrapper around bind(2) and setsockopt(2).

        Parameters:
        host(str): Host address.
        port(int): Port number.

        Returns:
        None.
        """
        logger.debug(f"[Socket] Binding to {host}:{port}...")
        self.skt.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.skt.bind((host, port))
        logger.debug(f"[Socket] Bound to {host}:{port}.")

    def listen(self, queue: int = 10) -> None:
        """
        Marks a connection-mode socket, specified by the socket argument, as
        accepting connections.
        Wrapper around listen(2).

        Parameters:
        queue(int): Max size for waiting queue.

        Returns:
        None.
        """
        self.skt.listen(queue)

    def accept(self):
        """
        Accepts one connection from the waiting queue, uses the file
        descriptor to create a peet Socket, and then starts a
        ClientHandler for it.
        Wrapper around accept(2).

        Parameters:
        None

        Returns:
        peer(Socket): Peer socket for connected client.
        """
        logger.debug("[Socket] Accepting client...")
        peer, addr = self.skt.accept()
        logger.debug(f"[Socket] Client accepted from {addr[0]}:{addr[1]}.")
        return addr, Socket(peer)

    def close(self) -> None:
        """
        Shutdowns and closes the socket, releasing resources.
        Wrapper around shutdown(2) and close(2).

        Parameters:
        None.

        Returns:
        None.
        """
        try:
            logger.debug("[Socket] Closing socket...")
            self.skt.shutdown(SHUT_RDWR)
            self.skt.close()
            logger.debug("[Socket] Socket closed.")
        except OSError:
            return

    def send(self, data: bytearray) -> None:
        """
        Loops until all data is sent through the socket.
        Similar to send_all socket method.

        Parameters:
        data(bytearray): Data in binary format.

        Returns:
        None.
        """
        total_bytes = len(data)
        bytes_sent = 0
        while bytes_sent < total_bytes:
            last_sent = self.skt.send(data[bytes_sent:])
            stats['bytes']['sent'] += last_sent
            if last_sent == 0:
                raise RuntimeError("Socket closed by the peer.")

            bytes_sent += last_sent

    def recv(self, size: int) -> bytearray:
        """
        Loops until size bytes of data are received through the socket.
        Similar to recv_all socket method.

        Parameters:
        size(int): The size of buffer that need to be stored.

        Returns: Array of binary data received.
        """
        data = []
        bytes_recd = 0
        while bytes_recd < size:
            segment = self.skt.recv(size - bytes_recd)
            stats['bytes']['recd'] += len(segment)
            if segment == b'':
                raise RuntimeError("Socket closed by the peer.")
            data.append(segment)
            bytes_recd += len(segment)

        return b''.join(data)

    def __del__(self):
        """
        Destructor for releasing resources in case something goes wrong.
        Wrapper around close(2).
        """
        self.close()
