import logging

DEBUG_LEVEL = logging.DEBUG
INFO_LEVEL = logging.INFO
FATAL_LEVEL = logging.FATAL

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")

logger = logging.getLogger()
