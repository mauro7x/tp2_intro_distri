from os import SEEK_END
from typing import Optional

# Lib
from lib.progress import progress_bar
from lib.logger import logger, FATAL_LEVEL
from lib.rdt_interface import RDTInterface

# -----------------------------------------------------------------------------
# constants

# config
INT_ENCODING = 'big'

# opcodes
UPLOAD_FILE_OP = 0
DOWNLOAD_FILE_OP = 1
LIST_FILES_OP = 2

# status codes
NO_ERR = 0
UNKNOWN_OP_ERR = 1
FILE_NOT_FOUND_ERR = 2

# sizes
OPCODE_SIZE = 1
STATUS_SIZE = 1
INT_SIZE = 8
CHUNK_SIZE = 2**16
MAX_STR_SIZE = 2**9  # 512
REQUEST_MSG_SIZE = OPCODE_SIZE + INT_SIZE + MAX_STR_SIZE

# -----------------------------------------------------------------------------
# encoders/decoders


def encode_short(i: int) -> bytearray:
    return i.to_bytes(1, INT_ENCODING)


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


def encode_filename(str: str) -> bytearray:
    """
    Safe encoding for strings (given the maximum size is MAX_STR_SIZE)
    """
    return str.encode()[:MAX_STR_SIZE-1] + b'\0'


def decode_filename(bytes: bytearray) -> str:
    str = bytes.decode()
    return str[:str.find('\0')]


def add_padding(bytes: bytearray, size: int) -> bytearray:
    return bytes + b'0'*(size - len(bytes))


# -----------------------------------------------------------------------------
# wrappers

# Requests


def download_request(rdt: RDTInterface, filename: str) -> int:
    """
    Send and validate a download request to the server.

    Parameters:
    rdt(RDTInterface): A reliable data transfer object.
    filename(str): namefile requested.

    Returns:
    filesize(int): size of the file to be downloaded.
    """
    message = encode_short(DOWNLOAD_FILE_OP) + encode_filename(filename)
    rdt.send(add_padding(message, REQUEST_MSG_SIZE))

    response = rdt.recv(STATUS_SIZE + INT_SIZE)
    status = decode_int(response[:STATUS_SIZE])
    if status > 0:
        raise RuntimeError(get_error_msg(status))

    filesize = decode_int(response[STATUS_SIZE:])
    return filesize


def download_response(rdt: RDTInterface, filesize: int) -> None:
    """
    Send file availability and filesize to a client.
    """
    message = encode_short(NO_ERR) + encode_int(filesize)
    rdt.send(message)
    return


def upload_request(rdt: RDTInterface, filename: str, filesize: int) -> None:
    """
    Send an upload request (with file information) to the server
    and validate the response.

    Parameters:
    rdt(RDTInterface): A reliable data transfer object.
    filename(str): namefile requested.
    filesize(int): size of the file to be uploaded.

    Returns:
    None
    """
    message = encode_short(UPLOAD_FILE_OP) + \
        encode_int(filesize) + encode_filename(filename)
    rdt.send(add_padding(message, REQUEST_MSG_SIZE))

    status = decode_int(rdt.recv(STATUS_SIZE))
    if status > 0:
        raise RuntimeError(get_error_msg(status))
    return


def upload_response(rdt: RDTInterface) -> None:
    """
    All-good response for an upload request.
    """
    rdt.send(encode_short(NO_ERR))
    return


def listfiles_request(rdt: RDTInterface) -> None:
    """
    Send the list files request to the server.

    Parameters:
    rdt(RDTInterface)

    Returns:
    None
    """
    rdt.send(add_padding(encode_short(LIST_FILES_OP), REQUEST_MSG_SIZE))
    return


def recv_request(rdt: RDTInterface) -> Optional[dict]:
    """
    Receive the operation code and parameters.

    Parameters:
    rdt(RDTInterface): .

    Returns:
    op_code(int): Request op code.
    args(dict): In case of a known request, return a dictionary with necessary
    arguments. (Unknown requests will return the plain bytearray)
    """
    request = rdt.recv(REQUEST_MSG_SIZE)
    op_code = decode_int(request[:OPCODE_SIZE])

    args = {}
    if op_code == DOWNLOAD_FILE_OP:
        args["filename"] = decode_filename(request[OPCODE_SIZE:])
    elif op_code == UPLOAD_FILE_OP:
        args["filesize"] = decode_int(
            request[OPCODE_SIZE:OPCODE_SIZE+INT_SIZE])
        args["filename"] = decode_filename(
            request[OPCODE_SIZE + INT_SIZE:])
    elif op_code == LIST_FILES_OP:
        pass
    else:
        return op_code, request[OPCODE_SIZE:]

    return op_code, args


def send_file(rdt: RDTInterface, f, progress: bool = False):
    """
    Send the file with binay format.

    Parameters:
    rdt(RDTInterface): .
    f(FILE): The file.
    [progress(bool)]: Flag for showing the progress bar.

    Returns:
    None
    """
    progress &= logger.level < FATAL_LEVEL

    sent = 0
    if progress:
        f.seek(0, SEEK_END)
        filesize = f.tell()
        f.seek(0)
        progress_bar(sent, filesize)
    chunk = f.read(CHUNK_SIZE)
    last_chunk = False
    while chunk:
        if len(chunk) < CHUNK_SIZE:
            last_chunk = True
        rdt.send(chunk, last_chunk)
        sent += len(chunk)
        if progress:
            progress_bar(sent, filesize)
        chunk = f.read(CHUNK_SIZE)

    if progress:
        print()


def recv_file(rdt: RDTInterface, filesize: int, progress: bool = False):
    """
    Create an iterator to recive a file.

    Parameters:
    rdt(RDTInterface): .
    [progress(bool)]: Flag for showing the progress bar.

    Returns:
    file_chunk(bytearray): A file chunk in binary format.
    """
    progress &= logger.level < FATAL_LEVEL

    recd = 0
    if progress:
        progress_bar(recd, filesize, True)
    while recd < filesize:
        file_chunk = rdt.recv(min(filesize - recd, CHUNK_SIZE))
        recd += len(file_chunk)
        if progress:
            progress_bar(recd, filesize, True)
        yield file_chunk

    if progress:
        print()


def send_list(rdt: RDTInterface, list: list) -> None:
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

    rdt.send(encode_short(NO_ERR) + encode_int(len(bytes)))
    chunks = [bytes[i:i+CHUNK_SIZE] for i in range(0, len(bytes), CHUNK_SIZE)]

    last_chunk = False
    for i, chunk in enumerate(chunks):
        if i == len(chunks) - 1:
            last_chunk = True

        rdt.send(chunk, last_chunk)


def recv_list(rdt: RDTInterface) -> list:
    """
    Receives and return a list of files.

    Parameters:
    rdt(RDTInterface): .

    Returns:
    list(list(tuple)): List of information about the file. [('filename', size,
                       last_mtime), ...]
    """
    total_len = decode_int(rdt.recv(INT_SIZE))

    chunks = []
    recd = 0
    while recd < total_len:
        chunk = rdt.recv(min(total_len - recd, CHUNK_SIZE))
        recd += len(chunk)
        chunks.append(chunk.decode())

    if chunks:
        return list(map(eval, (''.join(chunks)).split('\n')))
    return []

# -----------------------------------------------------------------------------
# error msgs


def send_file_not_found(rdt: RDTInterface) -> None:
    rdt.send(add_padding(encode_short(FILE_NOT_FOUND_ERR), CHUNK_SIZE))
    return


def send_unknown_error(rdt: RDTInterface) -> None:
    rdt.send(add_padding(encode_short(UNKNOWN_OP_ERR), CHUNK_SIZE))
    return


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
