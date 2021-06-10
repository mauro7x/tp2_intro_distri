from os import getenv
# Lib
from lib.logger import logger
from lib.go_back_n_v1 import GoBackNV1
from lib.go_back_n_v2 import GoBackNV2
from lib.stop_and_wait import StopAndWait

RDT_VERSION = getenv("RDT_VERSION", 'gbn')

printed = False


def create_rdt(send, recv):
    global printed
    if RDT_VERSION == 'gbn1':
        r = GoBackNV1(send, recv)
    elif RDT_VERSION == 's&w':
        r = StopAndWait(send, recv)
    else:
        r = GoBackNV2(send, recv)

    if not printed:
        selected = r.__class__.__name__
        logger.info(f'=== SELECTED RDT: {selected} ===')
        printed = True

    return r
