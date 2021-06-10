# Lib
from lib.rdt_interface import TIMEOUT

ALPHA = 1/8
BETA = 1/4


class RTTHandler:

    def __init__(self, initial=TIMEOUT) -> None:
        self.initial_timeout = initial
        self.timeout = initial
        self.mean_rtt = initial
        self.std_rtt = BETA * initial
        return

    def get_timeout(self) -> float:
        return self.timeout

    def add_sample(self, sample: float) -> None:
        self.mean_rtt = (1 - ALPHA) * self.mean_rtt + ALPHA * sample
        self.std_rtt = (1 - BETA) * self.std_rtt + BETA * sample
        self.timeout = min(self.initial_timeout,
                           self.mean_rtt + 4 * self.std_rtt)
        return

    def timed_out(self):
        self.timeout = min(self.initial_timeout, self.timeout * 2)
        return
