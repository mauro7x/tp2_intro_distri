# Lib
from lib.logger import logger
from lib.go_back_n_v1 import GoBackNV1
from lib.go_back_n_v2 import GoBackNV2
from lib.go_back_n_v3 import GoBackNV3
from lib.stop_and_wait import StopAndWait

RDT_VERSION = 'gbn'


def create_rdt(send, recv):
    if RDT_VERSION == 'gbn1':
        r = GoBackNV1(send, recv)
    elif RDT_VERSION == 'gbn2':
        r = GoBackNV2(send, recv)
    elif RDT_VERSION == 's&w':
        r = StopAndWait(send, recv)
    else:
        r = GoBackNV3(send, recv)

    selected = r.__class__.__name__
    logger.info(f'=== SELECTED RDT: {selected} ===')

    return r
