# Lib
from lib.stop_and_wait import StopAndWait
from lib.go_back_n import GoBackN

USE_GBN = True


def create_rdt(send, recv):
    if USE_GBN:
        return GoBackN(send, recv)
    else:
        return StopAndWait(send, recv)
