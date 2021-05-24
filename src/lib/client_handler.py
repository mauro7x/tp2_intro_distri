from collections import deque
from os import listdir, path
from threading import Condition, Thread
from itertools import count as it_count
from lib.logger import logger
from lib.stats import stats
import lib.protocol as prt
from lib.rdt_selection import create_rdt


class ClientHandler:

    id_it = it_count()

    def __init__(self, send, addr):
        self.id = next(ClientHandler.id_it)
        self.addr = addr
        self.th = Thread(None, self._run, self)
        self.queue_cv = Condition()
        self.queue = deque()
        self.rdt = create_rdt(send, self.pop)
        self.running = True
        self.th.start()

    def _handle_upload_file(self) -> None:
        stats["requests"]["upload-file"] += 1
        prt.send_status(self.rdt, prt.NO_ERR)

        filename = prt.recv_filename(self.rdt)

        with open(filename, 'wb') as f:
            for file_chunk in prt.recv_file(self.rdt):
                f.write(file_chunk)

        logger.info(
            f"File {filename} uploaded from {self.addr[0]}:{self.addr[1]}.")
        stats["files"]["uploads"] += 1

    def _handle_download_file(self) -> None:
        stats["requests"]["download-file"] += 1
        prt.send_status(self.rdt, prt.NO_ERR)

        filename = prt.recv_filename(self.rdt)

        try:
            with open(filename, 'rb') as f:
                prt.send_status(self.rdt, prt.NO_ERR)
                prt.send_file(self.rdt, f)
                stats["files"]["downloads"] += 1
                logger.info(
                    f"File {filename} downloaded from " +
                    f"{self.addr[0]}:{self.addr[1]}."
                )
        except FileNotFoundError:
            prt.send_status(self.rdt, prt.FILE_NOT_FOUND_ERR)

    def _handle_list_files(self) -> None:
        stats["requests"]["list-files"] += 1
        prt.send_status(self.rdt, prt.NO_ERR)

        files_list = []
        for file in listdir():
            if path.isdir(file):
                continue
            files_list.append((file, path.getsize(file), path.getmtime(file)))

        prt.send_list(self.rdt, files_list)

        logger.info(
            f"Files list downloaded from {self.addr[0]}:{self.addr[1]}.")

    def _run(self):
        logger.debug(f"[ClientHandler:{self.id}] Started.")

        opcode = prt.recv_opcode(self.rdt)

        if opcode == prt.UPLOAD_FILE_OP:
            self._handle_upload_file()

        elif opcode == prt.DOWNLOAD_FILE_OP:
            self._handle_download_file()

        elif opcode == prt.LIST_FILES_OP:
            self._handle_list_files()

        else:
            prt.send_status(self.rdt, prt.UNKNOWN_OP_ERR)

        logger.debug(f"[ClientHandler:{self.id}] Finished.")
        self.running = False
        return

    def push(self, data):
        with self.queue_cv:
            self.queue.append(data)
            self.queue_cv.notify()
        return

    def pop(self, length):
        result = []
        total = 0
        with self.queue_cv:
            while total < length:
                while not self.queue:
                    self.queue_cv.wait()
                result.append(self.queue.popleft())
                total += len(result[-1])

        result = b''.join(result)
        if total - length:
            self.queue.appendleft(result[length:])
            result = result[:length]

        return result

    def join(self, force=False):
        if force:
            logger.debug(f"[ClientHandler:{self.id}] Forcing join.")
            self.rdt.close()
            self.running = False

        self.th.join()
        logger.debug(f"[ClientHandler:{self.id}] Joined.")

    def is_done(self):
        return not self.running
