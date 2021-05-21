# parse.py
from argparse import ArgumentParser
from __main__ import __doc__ as description, __file__
from lib.logger import DEBUG_LEVEL, INFO_LEVEL, FATAL_LEVEL
from lib.constants import DEFAULT_ADDR, DEFAULT_PORT


def _parse_args(add_args=None):
    """
    Parse args using `argparse` in order to fullfil requirements.
    """

    parser = ArgumentParser(description=description, prog=__file__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_const",
                       dest="level", const=DEBUG_LEVEL, default=INFO_LEVEL,
                       help="Increase output verbosity")
    group.add_argument("-q", "--quiet", action="store_const",
                       dest="level", const=FATAL_LEVEL,
                       help="Decrease output verbosity")
    parser.add_argument("-H", "--host", dest="ADDR", type=str,
                        default=DEFAULT_ADDR, help="service IP address")
    parser.add_argument("-p", "--port", dest="PORT", type=int,
                        default=DEFAULT_PORT, help="service port")

    if add_args is not None:
        add_args(parser)
    return parser.parse_args()


def _add_name_arg(parser):
    parser.add_argument("-n", "--name", dest="FILENAME", type=str,
                        required=True, help="file name")


def _args_upload(parser):
    parser.add_argument("-s", "--src", dest="FILEPATH", type=str,
                        required=True, help="source file path")
    _add_name_arg(parser)


def parse_args_upload():
    return _parse_args(_args_upload)


def _args_download(parser):
    parser.add_argument("-d", "--dst",  dest="FILEPATH", type=str,
                        required=True, help="destination file path")
    _add_name_arg(parser)


def parse_args_download():
    return _parse_args(_args_download)


def _args_list(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-n", "--by-name", action="store_const",
                       dest="SORT_KEY", const="name", default="name",
                       help="sort by file name")
    group.add_argument("-s", "--by-size", action="store_const",
                       dest="SORT_KEY", const="size",
                       help="sort by file size")
    group.add_argument("-d", "--by-date", action="store_const",
                       dest="SORT_KEY", const="date",
                       help="sort by last modified date")

    parser.add_argument("-a", "--ascending", action="store_true",
                        dest="ASC", default=False,
                        help="use ascending sort (default: descending)")


def parse_args_list():
    return _parse_args(_args_list)
