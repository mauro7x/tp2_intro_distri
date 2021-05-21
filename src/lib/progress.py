# Basic progress bar implementation
from sys import stdout
from lib.formatters import get_size_readable


def progress_bar(current, total, inverted=False, bar_length=20):
    percent = int(100 * (current / total if total > 0 else 1))
    perlength = int(bar_length * percent / 100)
    progress = '=' * perlength
    remaining = ' ' * (bar_length - perlength)

    c_size = get_size_readable(current, False)
    t_size = get_size_readable(total, False)

    if inverted:
        stdout.write(
            f"\r[{remaining}<{progress}] {percent}% ({c_size}/{t_size})")
    else:
        stdout.write(
            f"\r[{progress}>{remaining}] {percent}% ({c_size}/{t_size})")

    stdout.flush()
