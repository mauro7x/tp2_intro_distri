import time
from io import SEEK_END


def get_size_readable(size: int, decimals: bool = True) -> str:
    assert size >= 0

    if size < 1e3:
        unit = "B"
        converted = size
    elif size < 1e6:
        unit = "KB"
        converted = (size / (1e3))
    else:
        unit = "MB"
        converted = (size / (1e6))

    if decimals:
        return f"{converted:.2f} {unit}"
    else:
        return f"{int(converted)} {unit}"


def get_time_readable(seconds: float) -> str:
    if seconds < 10:
        return f'00:0{seconds:.4f}'
    return time.strftime('%M:%S', time.gmtime(seconds))


def filesize(filename: str) -> int:
    f = open(filename)
    f.seek(0, SEEK_END)
    size = f.tell()
    f.close()
    return size
