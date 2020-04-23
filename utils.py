#!/usr/bin/env python3
import requests
import logging

logger = logging.getLogger()
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


if __name__ == "__main__":
    # for ip, dev in getAgilent().items():
    data = getAgilent()
    for device, channel_name, channel_data in getChannels(data):
        print(device, channel_name, channel_data["prefix"])
