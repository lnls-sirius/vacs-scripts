#!/usr/bin/env python3
import argparse
import epics
import logging
import math
import asyncio
import sys

from datetime import timedelta, datetime
from utils import getAgilent, getDevices, getChannels, TIMEFMT

from qtpy.QtCore import QObject, Signal, QRunnable

logger = logging.getLogger()

EPICS_TOUT = 1
CMD_TOUT = 0.500

FIXED, STEP, STEP_TO_FIXED = "fixed", "step", "step_to_fixed"


class AgilentAsync(QObject):
    timerStatus = Signal(dict)
    started = Signal()
    finished = Signal()

    def __init__(self, *args, **kwargs):
        super(AgilentAsync, self).__init__(*args, **kwargs)

    async def toFixed(
        self, dev, chs, voltage,
    ):
        self.timerStatus.emit({"dev": dev, "status": "to Fixed"})

        pv, val = dev + ":Step-SP_Backend", 0
        logger.info("set {} {}".format(pv, val))
        # epics.caput(pv, val, timeout=EPICS_TOUT)
        await asyncio.sleep(CMD_TOUT)

        for ch in chs:
            pv, val = ch + ":VoltageTarget-SP", voltage
            logger.info("set {} {}".format(pv, val))
            # epics.caput(pv, val, timeout=EPICS_TOUT)
            await asyncio.sleep(CMD_TOUT)
        self.timerStatus.emit({"dev": dev, "status": "Done"})

    async def toStep(
        self, dev, chs,
    ):
        self.timerStatus.emit({"dev": dev, "status": "to Step"})

        pv, val = dev + ":Step-SP_Backend", 15
        logger.info("set {} {}".format(pv, val))
        # epics.caput(pv, val, timeout=EPICS_TOUT)
        self.timerStatus.emit({"dev": dev, "status": "Done"})
        await asyncio.sleep(CMD_TOUT)

    async def toStepToFix(self, _delay, dev, chs, voltage):
        """ Run a function then another ..."""
        delay = timedelta(seconds=_delay)
        t_ini = datetime.now()

        tick = math.ceil(_delay / 100)

        logger.info(
            'Running initial function "{}" at {} for device "{}". Next method in {} seconds.'.format(
                self.toStep.__name__, t_ini.strftime(TIMEFMT), dev, _delay
            )
        )
        await self.toStep(dev, chs)

        t_now = datetime.now()
        t_elapsed = t_now - t_ini
        while t_elapsed < delay:
            remaining = delay - t_elapsed
            logger.info("Time remaining {} for device {}.".format(remaining, dev))
            self.timerStatus.emit({"dev": dev, "status": remaining})
            await asyncio.sleep(tick)

            t_now = datetime.now()
            t_elapsed = t_now - t_ini

        logger.info(
            'Running final function "{}" at {} for device "{}".'.format(
                self.toFixed.__name__, datetime.now().strftime(TIMEFMT), dev
            )
        )

        await self.toFixed(dev, chs, voltage)

    async def handle(self, mode, step_to_fixed_delay, voltage, devices):

        tasks = []
        for device in devices:
            dev = device["prefix"]
            chs = [ch["prefix"] for ch_name, ch in device["channels"].items()]

            if sys.version_info >= (3, 7):

                if mode == FIXED:
                    tasks.append(
                        asyncio.create_task(self.toFixed(dev, chs, voltage=voltage,))
                    )

                elif mode == STEP:
                    tasks.append(asyncio.create_task(self.toStep(dev, chs,)))

                elif mode == STEP_TO_FIXED:
                    tasks.append(
                        asyncio.create_task(
                            self.toStepToFix(step_to_fixed_delay, dev, chs, voltage)
                        )
                    )
            else:
                loop = asyncio.get_event_loop()
                if mode == FIXED:
                    tasks.append(
                        loop.create_task(self.toFixed(dev, chs, voltage=voltage,))
                    )

                elif mode == STEP:
                    tasks.append(loop.create_task(self.toStep(dev, chs,)))

                elif mode == STEP_TO_FIXED:
                    tasks.append(
                        loop.create_task(
                            self.toStepToFix(step_to_fixed_delay, dev, chs, voltage)
                        )
                    )

        await asyncio.gather(*tasks)

    def asyncStart(
        self, mode, step_to_fixed_delay, voltage, devices,
    ):
        if sys.version_info >= (3, 7):
            asyncio.run(
                self.handle(
                    mode=mode,
                    step_to_fixed_delay=step_to_fixed_delay,
                    voltage=voltage,
                    devices=devices,
                )
            )
        else:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self.handle(
                    mode=mode,
                    step_to_fixed_delay=step_to_fixed_delay,
                    voltage=voltage,
                    devices=devices,
                )
            )
            loop.close()


class AgilentAsyncRunnable(QRunnable):
    def __init__(
        self, agilentAsync: AgilentAsync, mode, step_to_fixed_delay, voltage, devices,
    ):
        super(AgilentAsyncRunnable, self).__init__()
        self.agilentAsync = agilentAsync
        self.mode = mode
        self.step_to_fixed_delay = step_to_fixed_delay
        self.voltage = voltage
        self.devices = devices

    def run(self):
        self.agilentAsync.started.emit()
        try:
            self.agilentAsync.asyncStart(
                mode=self.mode,
                step_to_fixed_delay=self.step_to_fixed_delay,
                voltage=self.voltage,
                devices=self.devices,
            )
        except Exception:
            logger.exception("Unexpected Error")
        finally:
            self.agilentAsync.finished.emit()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d,%H:%M:%S",
    )
    parser = argparse.ArgumentParser(
        """Utilitário para Agilent4UHV
            Configura tensão dos canais e o modo de operação do dispositivo."""
    )
    parser.add_argument(
        "--mode",
        choices=[FIXED, STEP, STEP_TO_FIXED],
        required=True,
        help="""Modo de operação do dispositivo (fixed/step/step_to_fixed).
        No modo fixed, a bomba é configurada para tensão fixa e o valor de tensão é ajustado conforme o parâmetro \"--voltage\".
        No modo step a bomba é configurada para tensão em step.
        No modo step_to_fixed a bomba é configurada em step e após um certo delay conforme o parâmetro \"--step-to-fixed-delay\" é configurada em tensão fixa conforme o parâmetro \"--voltage\".""",
        type=str,
    )
    parser.add_argument(
        "--voltage",
        help="Tensão dos canais em modo fixo de 3000 a 7000. O ajuste é feito somente nos modos 'fixed e step_to_fixed'.",
        type=int,
        default=3000,
    )
    parser.add_argument(
        "--step-to-fixed-delay",
        help='Delay em segundos entre a transição do modo step para fixed quando "--mode" for "step_to_fixed".',
        type=float,
        default=600.0,
        dest="step_to_fixed_delay",
    )

    args = parser.parse_args()

    if args.voltage < 3000 or args.voltage > 7000:
        raise ValueError("Voltage must be between 3000 and 7000.")
    if args.step_to_fixed_delay < 0:
        raise ValueError('Parameter "--step-to-fixed-delay" cannot be less then zero.')

    data = getAgilent()
    devices = [device for device in getDevices(data)]
    agilentAsyn = AgilentAsync()
    agilentAsyn.asyncStart(
        mode=args.mode,
        step_to_fixed_delay=args.step_to_fixed_delay,
        voltage=args.voltage,
        devices=devices,
    )
