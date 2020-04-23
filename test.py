#!/usr/bin/env python3
import logging
import threading
import time
import math
from utils import TIMEFMT

logger = logging.getLogger()


def f1():
    logger.info("Hello!")


def f2():
    logger.info("Bye!")


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d,%H:%M:%S",
    )
    t = threading.Thread(target=lauchTimer, daemon=True, args=[10, f1, f2], kwargs={})
    t.start()

    while True:
        time.sleep(1)
