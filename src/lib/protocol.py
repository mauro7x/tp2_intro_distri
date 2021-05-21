from os import SEEK_END
from lib.socket_tcp import Socket
from lib.progress import progress_bar
from lib.logger import logger, FATAL_LEVEL

# -----------------------------------------------------------------------------
# constants

# config
INT_ENCODING = 'big'

# sizes
OPCODE_SIZE = 1
STATUS_SIZE = 1
INT_SIZE = 8
CHUNK_SIZE = 1024

# opcodes
UPLOAD_FILE_OP = 0
DOWNLOAD_FILE_OP = 1
LIST_FILES_OP = 2

# status codes
NO_ERR = 0
UNKNOWN_OP_ERR = 1
FILE_NOT_FOUND_ERR = 2

# -----------------------------------------------------------------------------
# encoders/decoders


def encode_int(i: int) -> bytearray:
    """
    Encode the integer type value to binary type.

    Parameters:
    i(int): An integer number.

    Returns:
    bytes(bytearray): A binary value.
    """

    return i.to_bytes(INT_SIZE, INT_ENCODING)


def decode_int(bytes: bytearray) -> int:
    """
    Decode the binary value to an integer value.

    Parameters:
    bytes(bytearray): Binary value.

    Returns:
    i(int): An integer number.
    """
    return int.from_bytes(bytes, INT_ENCODING)

# -----------------------------------------------------------------------------
# wrappers


def send_status(skt: Socket, status: int) -> None:
    """
    Send the opcode of status in binary format.

    Parameters:
    skt(Socket): Socket.
    status(int): Opcode of status.

    Returns:
    None
    """
    skt.send(status.to_bytes(STATUS_SIZE, INT_ENCODING))


def recv_status(skt: Socket) -> int:
    """
    Receive the status opcode and return it with integer value.

    Parameters:
    skt(Socket): Socket.

    Returns:
    opcode(int): Opcode of status.
    """
    return int.from_bytes(skt.recv(STATUS_SIZE), INT_ENCODING)


def send_opcode(skt: Socket, opcode: int) -> None:
    """
    Send the command opcode in binary format.

    Parameters:
    skt(Socket): Socket.
    status(int): Command opcode

    Returns:
    None
    """
    skt.send(opcode.to_bytes(OPCODE_SIZE, INT_ENCODING))


def recv_opcode(skt: Socket) -> int:
    """
    Receives the command opcode and return it with integer value.

    Parameters:
    skt(Socket): Socket.

    Returns:
    opcode(int): Command opcode.
    """
    return int.from_bytes(skt.recv(OPCODE_SIZE), INT_ENCODING)


def send_filename(skt: Socket, filename: str) -> None:
    """
    Send the filename with binary format.

    Parameters:
    skt(Socket): Socket.
    filename(str): the name of file, must be open with binary ('b') mode.

    Returns:
    None
    """
    bytes = filename.encode()
    skt.send(encode_int(len(bytes)))
    skt.send(bytes)


def recv_filename(skt: Socket) -> str:
    """
    Receives the filename and return it with string type.

    Parameters:
    skt(Socket): Socket.

    Returns:
    filename(str): The name of file.
    """
    filename_size = decode_int(skt.recv(INT_SIZE))
    filename = skt.recv(filename_size).decode()
    return filename


def send_file(skt: Socket, f, progress: bool = False):
    """
    Send the file with binay format.

    Parameters:
    skt(Socket): Socket.
    f(FILE): The file.
    [progress(bool)]: Flag for showing the progress bar.

    Returns:
    None
    """
    progress &= logger.level < FATAL_LEVEL

    f.seek(0, SEEK_END)
    filesize = f.tell()
    f.seek(0)

    skt.send(encode_int(filesize))

    sent = 0
    if progress:
        progress_bar(sent, filesize)
    chunk = f.read(CHUNK_SIZE)
    while chunk:
        skt.send(chunk)
        sent += len(chunk)
        if progress:
            progress_bar(sent, filesize)
        chunk = f.read(CHUNK_SIZE)

    if progress:
        print()


def recv_file(skt: Socket, progress: bool = False):
    """
    Create an iterator to recive a file.

    Parameters:
    skt(Socket): Socket.
    [progress(bool)]: Flag for showing the progress bar.

    Returns:
    file_chunk(bytearray): A file chunk in binary format.
    """
    progress &= logger.level < FATAL_LEVEL

    filesize = decode_int(skt.recv(INT_SIZE))
    if filesize < 0:
        pass

    recd = 0
    if progress:
        progress_bar(recd, filesize, True)
    while recd < filesize:
        file_chunk = skt.recv(min(filesize - recd, CHUNK_SIZE))
        recd += len(file_chunk)
        if progress:
            progress_bar(recd, filesize, True)
        yield file_chunk

    if progress:
        print()


def send_list(skt: Socket, list: list) -> None:
    """
    Send the list of files information about the file with binary format.

    Parameters:
    skt(Socket):Socket.
    list(list(tuple)): List of information about the file [('filename', size,
                       last_mtime), ...]

    Returns:
    None
    """
    bytes = ('\n'.join(map(str, list))).encode()

    skt.send(encode_int(len(bytes)))
    chunks = [bytes[i:i+CHUNK_SIZE] for i in range(0, len(bytes), CHUNK_SIZE)]

    for chunk in chunks:
        skt.send(chunk)


def recv_list(skt: Socket) -> list:
    """
    Receives and return a list of files.

    Parameters:
    skt(Socket): Socket.

    Returns:
    list(list(tuple)): List of information about the file. [('filename', size,
                       last_mtime), ...]
    """
    total_len = decode_int(skt.recv(INT_SIZE))

    chunks = []
    recd = 0
    while recd < total_len:
        chunk = skt.recv(min(total_len - recd, CHUNK_SIZE))
        recd += len(chunk)
        chunks.append(chunk.decode())

    if chunks:
        return list(map(eval, (''.join(chunks)).split('\n')))
    return []

# -----------------------------------------------------------------------------
# error msgs


def get_error_msg(err_code: int) -> str:
    """
    Receives the error code and return the related message.

    Parameters:
    err_code(int): The error code.

    Returns:
    mensaje(str): The error message.
    """
    if err_code == UNKNOWN_OP_ERR:
        return "Opcode desconocido por el servidor."
    elif err_code == FILE_NOT_FOUND_ERR:
        return "El archivo no existe en el servidor."

    return ""


# -----------------------------------------------------------------------------
