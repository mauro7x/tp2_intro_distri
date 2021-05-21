# idea: keep track of some interesting stats
# to show when server is closed

from datetime import datetime
from lib.formatters import get_size_readable

stats = {
    "connections": 0,
    "requests": {
        "upload-file": 0,
        "download-file": 0,
        "list-files": 0,
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
    print(f"> Established connections: {stats['connections']}")

    print("> Requests:")
    requests = stats['requests']
    print(f"  * upload-file: {requests['upload-file']}")
    print(f"  * download-file: {requests['download-file']}")
    print(f"  * list-files: {requests['list-files']}")

    print("> Bytes transferred:")
    bytes = stats['bytes']
    print(f"  * Sent: {get_size_readable(bytes['sent'])}")
    print(f"  * Received: {get_size_readable(bytes['recd'])}")

    print("> Files:")
    files = stats['files']
    print(f"  * Uploads: {files['uploads']}")
    print(f"  * Downloads: {files['downloads']}")
    print("==========================================\n")
