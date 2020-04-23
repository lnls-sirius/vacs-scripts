#!/usr/bin/env python3
from datetime import timedelta, datetime
import requests

TIMEFMT = "%d/%m/%Y %H:%M:%S"

DEVICES_URL = "http://10.0.38.42:26001/devices"


def getMKS():
    return requests.get(DEVICES_URL, verify=False, params={"type": "mks"}).json()


def getAgilent():
    return requests.get(DEVICES_URL, verify=False, params={"type": "agilent"}).json()


def getDevices(data: dict):
    """ Generate (device data) """
    for ip, beagle in data.items():
        for device in beagle:
            yield device


def getChannels(data: dict):
    """ Generate tuples containing (device prefix, channel_name, channel_data) """
    for ip, beagle in data.items():
        for device in beagle:
            for channel_name, channel_data in device["channels"].items():
                yield device["prefix"], channel_name, channel_data


def lauchTimer(_delay, target1, target2, **kwargs):
    """ Run a function then another ..."""
    delay = timedelta(seconds=_delay)
    t_ini = datetime.now()
    logger.info(
        'Running initial function "{}" at {}. Next method in {} seconds.'.format(
            target1.__name__, t_ini.strftime(TIMEFMT), _delay
        )
    )

    t_now = datetime.now()
    t_elapsed = t_now - t_ini
    while t_elapsed < delay:
        logger.info("Time elapsed {}.".format(t_elapsed.strftime("%H:%M:%S")))
        time.sleep(1)

        t_now = datetime.now()
        t_elapsed = t_now - t_ini

    logger.info(
        'Running final function "{}" at {}.'.format(
            target2.__name__, t_ini.strftime(TIMEFMT)
        )
    )

    target1()


if __name__ == "__main__":
    # for ip, dev in getAgilent().items():
    data = getAgilent()
    for device, channel_name, channel_data in getChannels(data):
        print(device, channel_name, channel_data["prefix"])
