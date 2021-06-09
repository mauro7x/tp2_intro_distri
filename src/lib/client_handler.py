from collections import deque
from os import listdir, path
from threading import Condition, Thread
from itertools import count as it_count
from time import perf_counter as now
from typing import Optional

# Lib
from lib.logger import logger
from lib.misc import filesize
from lib.stats import stats
from lib.misc import get_size_readable, get_time_readable
from lib.rdt_selection import create_rdt
import lib.protocol as prt

# Exceptions
from lib.socket_udp import SocketTimeout


class ServerStopped(Exception):
    pass


class ClientHandler:

    id_it = it_count()

    def __init__(self, send, addr):
        self.id = next(ClientHandler.id_it)
        self.addr = addr
        self.queue_cv = Condition()
        self.queue = deque()
        self.rdt = create_rdt(send, self.pop)
        self.running = True
        self.th = Thread(target=self._run, name=f'ClientHandler:{self.id}')
        self.th.start()

    def _handle_download_file(self, args: dict) -> None:
        stats["requests"]["download-file"] += 1
        filename = args['filename']

        try:
            size = filesize(filename)
            prt.download_response(self.rdt, filesize(filename))
        except FileNotFoundError:
            prt.send_file_not_found(self.rdt)

        logger.info(
            f'File "{filename}" being downloaded from '
            f'{self.addr[0]}:{self.addr[1]}...')

        start = now()

        with open(filename, 'rb') as f:
            prt.send_file(self.rdt, f)

        stats["files"]["downloads"] += 1
        elapsed = now() - start
        logger.info(
            f'File "{filename}" downloaded from {self.addr[0]}:{self.addr[1]}'
            f' (elapsed: {get_time_readable(elapsed)}, avg transf speed: '
            f'{get_size_readable(size/elapsed)}/s).')

    def _handle_upload_file(self, args) -> None:
        stats["requests"]["upload-file"] += 1
        prt.upload_response(self.rdt)
        start = now()

        filename: str = args['filename']
        filesize: int = args['filesize']

        logger.info(
            f'Uploading file "{filename}" from '
            f'{self.addr[0]}:{self.addr[1]}...')

        with open(filename, 'wb') as f:
            for file_chunk in prt.recv_file(self.rdt, filesize):
                f.write(file_chunk)

        time_elapsed = (now() - start)
        logger.info(
            f'File "{filename}" uploaded from {self.addr[0]}:{self.addr[1]} '
            f'(elapsed: {get_time_readable(time_elapsed)}, avg transf speed: '
            f'{get_size_readable(filesize/time_elapsed)}/s).')
        stats["files"]["uploads"] += 1

    def _handle_list_files(self, args: dict) -> None:
        stats["requests"]["list-files"] += 1

        files_list = []
        for file in listdir():
            if path.isdir(file):
                # skipping subdirectories
                continue
            files_list.append((file, path.getsize(file), path.getmtime(file)))

        prt.send_list(self.rdt, files_list)

        logger.info(
            f"Files list sent to {self.addr[0]}:{self.addr[1]}.")

    def _run(self):
        try:
            logger.debug(f"[ClientHandler:{self.id}] Started.")

            opcode, args = prt.recv_request(self.rdt)

            if opcode == prt.DOWNLOAD_FILE_OP:
                logger.debug(
                    f"[ClientHandler:{self.id}] Handling "
                    "download-file request.")
                self._handle_download_file(args)

            elif opcode == prt.UPLOAD_FILE_OP:
                logger.debug(
                    f"[ClientHandler:{self.id}] Handling upload-file request.")
                self._handle_upload_file(args)

            elif opcode == prt.LIST_FILES_OP:
                logger.debug(
                    f"[ClientHandler:{self.id}] Handling list-files request.")
                self._handle_list_files(args)

            else:
                stats["requests"]["invalid"] += 1
                prt.send_unknown_error(self.rdt)

            logger.debug(f"[ClientHandler:{self.id}] Finished.")
            self.running = False
        except KeyboardInterrupt:
            pass
        except ServerStopped:
            pass
        except BaseException:
            logger.exception("Unexpected error during execution:")
        return

    def push(self, data):
        """
        Push some data to the queue. Thread-safe function.

        Parameters:
        data(bytearray): data chunk.

        Returns:
        None.
        """
        with self.queue_cv:
            self.queue.append(data)
            self.queue_cv.notify()
        return

    def pop(self, timeout: Optional[int] = None,
            start_time: Optional[int] = 0):
        """
        Pop one data package from the queue. Thread-safe function.
        Optionally, it can receive a timeout, so it will return when
        the data is found in the queue or when the timeout happens,
        whatever comes first.

        Parameters:
        [timeout(int)]: time to wait.
        [start_time(int)]: init time from the timer.

        Returns:
        data(bytearray): data package from the queue.
        """
        if not self.running:
            raise ServerStopped()

        with self.queue_cv:
            while not self.queue:
                wait_time = timeout - \
                    (now() - start_time) if timeout is not None else None

                if not self.queue_cv.wait(wait_time):
                    raise SocketTimeout()

        return self.queue.popleft()

    def join(self, force=False):
        if force:
            self.running = False

        self.th.join()
        logger.debug(f"[ClientHandler:{self.id}] Joined.")

    def is_done(self):
        return not self.running
