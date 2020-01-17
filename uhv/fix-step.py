#!/usr/bin/env python3
import epics
import re
import time
import argparse
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
                                datefmt='%Y-%m-%d,%H:%M:%S')
logger = logging.getLogger()

epics_tout = 1
cmd_tout = 0.500

FIXED, STEP = 'fixed', 'step'


if __name__ == '__main__':
    parser = argparse.ArgumentParser("""Utilitário para Agilent4UHV
            Configura tensão dos canais e o modo de operação do dispositivo.""")

    parser.add_argument('--device-list', required=True, help="Lista com os dispositivos/canais.", type=str)
    parser.add_argument('--voltage', choices=[3000,5000,7000], required=True, help="Tensão dos canais em modo fixo. Ajustado somente se o modo de operação for 'fixed'.", type=float)
    parser.add_argument('--mode', choices=[FIXED, STEP], required=True, help="Modo de operação do dispositivo (fixed/step).", type=str)
    args = parser.parse_args()

    voltage = args.voltage
    mode = args.mode
    device_list = args.device_list

    devices = []
    with open(device_list) as _f:
        devices = _f.readlines()

    for device in devices:
        pvs = re.sub('\s+', ' ', device).strip().replace('\n','').split(' ')
        dev = pvs[0]
        chs = pvs[1:]
        
        if mode == FIXED:
            pv, val = dev + ':Step-SP_Backend', 0
            logger.info('set {} {}'.format(pv, val))
            epics.caput(pv, val, timeout=epics_tout)
            time.sleep(cmd_tout)

            for ch in chs:
                pv, val = ch + ':VoltageTarget-SP', voltage
                logger.info('set {} {}'.format(pv, val))
                epics.caput(pv, val, timeout=epics_tout)
                time.sleep(cmd_tout)

        elif mode == STEP:
            pv, val = dev + ':Step-SP_Backend', 15
            logger.info('set {} {}'.format(pv, val))
            epics.caput(pv, val, timeout=epics_tout)
            time.sleep(cmd_tout)

