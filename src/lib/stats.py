from datetime import datetime

# Lib
from lib.misc import get_size_readable

stats = {
    "requests": {
        "upload-file": 0,
        "download-file": 0,
        "list-files": 0,
        "invalid": 0,
        "total": 0
    },
    "files": {
        "uploads": 0,
        "downloads": 0
    },
    "bytes": {
        "sent": 0,
        "recd": 0
    },
    "transfer-speeds": [],
    "start-time": datetime.now(),
    "runtime": 0
}


def mean(it):
    return sum(it)/len(it)


def std(it):
    avg = mean(it)
    return (sum(map(lambda x: (avg - x)**2, it)) ** 0.5) / (len(it) - 1)


def print_stats():
    stats["runtime"] = str(datetime.now() - stats["start-time"])
    print("\n===========================================")
    print("=                  STATS                  =")
    print("===========================================\n")
    print(f"> Run time: {stats['runtime']}")
    print()
    print("> Requests:")
    requests = stats['requests']
    print(f"  * upload-file: {requests['upload-file']}")
    print(f"  * download-file: {requests['download-file']}")
    print(f"  * list-files: {requests['list-files']}")
    print(f"  * invalid: {requests['invalid']}")
    print(f"  * total: {requests['total']}")
    print()
    print("> Bytes transferred:")
    bytes = stats['bytes']
    print(f"  * Sent: {get_size_readable(bytes['sent'])}")
    print(f"  * Received: {get_size_readable(bytes['recd'])}")
    print()
    print("> Transfer speeds:")
    transfer_speeds = stats['transfer-speeds']
    M = get_size_readable(max(transfer_speeds))
    m = get_size_readable(min(transfer_speeds))
    avg = get_size_readable(mean(transfer_speeds))
    dev = get_size_readable(std(transfer_speeds))
    print(f"  * min - max: {M}/s - {m}/s")
    print(f"  * avg - mdev: {avg}/s - {dev}/s")
    print()
    print("> Files:")
    files = stats['files']
    print(f"  * Uploads: {files['uploads']}")
    print(f"  * Downloads: {files['downloads']}")
    print("==========================================\n")
