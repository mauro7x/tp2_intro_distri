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
    "start-time": datetime.now(),
    "runtime": 0
}


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
    print("> Files:")
    files = stats['files']
    print(f"  * Uploads: {files['uploads']}")
    print(f"  * Downloads: {files['downloads']}")
    print("==========================================\n")
