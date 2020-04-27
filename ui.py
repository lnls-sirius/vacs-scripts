#!/usr/bin/env python3
import logging
from qtpy.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTableWidget,
    QHeaderView,
    QTableWidgetItem,
    QWidget,
)
from qtpy.QtGui import QRegExpValidator, QIntValidator, QDoubleValidator, QColor

from qtpy.QtCore import Qt, QRegExp, QObject, QThread, QThreadPool
from utils import getDevices, getAgilent
from agilent import (
    AgilentAsyncRunnable,
    AgilentAsync,
    STEP as MODE_STEP,
    FIXED as MODE_FIXED,
    STEP_TO_FIXED as MODE_STEP_TO_FIXED,
)

logger = logging.getLogger()


class Parameters(QFrame):
    def __init__(self, *args, **kwargs):
        super(Parameters, self).__init__(*args, **kwargs)
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.contentLayout = QGridLayout()

        self.voltage = 3000
        self.delay = 600.00

        self.setpointVoltageLabel = QLabel("Fixed voltage [3000 to 7000] V")
        self.setpointVoltageSettingLabel = QLabel()
        self.setpointVoltageInp = QLineEdit()
        self.setpointVoltageInp.setMaximumWidth(100)
        self.setpointVoltageInp.setValidator(QIntValidator(3000, 7000))
        self.setpointVoltageInp.setToolTip("New fixed voltage setpoint.")

        self.contentLayout.addWidget(self.setpointVoltageLabel, 0, 0, 1, 1)
        self.contentLayout.addWidget(self.setpointVoltageInp, 0, 1, 1, 1)
        self.contentLayout.addWidget(self.setpointVoltageSettingLabel, 0, 2, 1, 1)

        self.stepToFixDelayLabel = QLabel("Step to Fixed delay in seconds")
        self.stepToFixDelaySettingLabel = QLabel()
        self.stepToFixDelayInp = QLineEdit()
        self.stepToFixDelayInp.setMaximumWidth(100)
        self.stepToFixDelayInp.setValidator(QDoubleValidator(1, 1440, 2))
        self.stepToFixDelayInp.setToolTip("Delay between toStep and toFixed calls.")

        self.contentLayout.addWidget(self.stepToFixDelayLabel, 1, 0, 1, 1)
        self.contentLayout.addWidget(self.stepToFixDelayInp, 1, 1, 1, 1)
        self.contentLayout.addWidget(self.stepToFixDelaySettingLabel, 1, 2, 1, 1)

        self.setButton = QPushButton("Confirm")
        self.setButton.clicked.connect(self.confirm)
        self.setButton.setToolTip("Apply settings")
        self.contentLayout.addWidget(self.setButton, 3, 1, 1, 1)

        self.setLayout(self.contentLayout)
        self.confirm()

    def confirm(self):
        try:
            voltageString = self.setpointVoltageInp.text()
            tmp = int(voltageString)
            self.voltage = 3000 if tmp < 3000 else (7000 if tmp > 7000 else tmp)
        except ValueError:
            pass
        finally:
            self.setpointVoltageSettingLabel.setText("{} V".format(self.voltage))
        try:
            delayString = self.stepToFixDelayInp.text()
            tmp = float(delayString)
            self.delay = 1.0 if tmp < 1.0 else (1440.0 if tmp > 1440.0 else tmp)
        except ValueError:
            pass
        finally:
            self.stepToFixDelaySettingLabel.setText("{} s".format(self.delay))


class Devices(QFrame):
    def __init__(self, *args, **kwargs):
        super(Devices, self).__init__(*args, **kwargs)
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.contentLayout = QGridLayout()

        self.devices = []

        # Current Action Status
        self.status = {}

        self.devicePrefixFilterLabel = QLabel(
            "Device filter (Ion Pump not the channel!)"
        )
        self.devicePrefixFilterInp = QLineEdit()
        self.devicePrefixFilterInp.setMaximumWidth(100)

        self.updateDeviceListButton = QPushButton("Apply Filter")
        self.updateDeviceListButton.clicked.connect(self.updateDeviceList)
        self.updateDeviceListButton.setToolTip("Filter the device prefix list.")

        self.contentLayout.addWidget(self.devicePrefixFilterLabel, 0, 0, 1, 2)
        self.contentLayout.addWidget(self.devicePrefixFilterInp, 1, 0, 1, 1)
        self.contentLayout.addWidget(self.updateDeviceListButton, 1, 1, 1, 1)

        self.deviceList = QListWidget()
        self.contentLayout.addWidget(self.deviceList, 2, 0, 2, 2)

        self.deviceStatus = QTableWidget()
        self.deviceStatus.setColumnCount(2)
        self.deviceStatus.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.deviceStatus.setHorizontalHeaderLabels(["Device", "Status"])
        self.deviceStatusLabel = QLabel("Status")

        self.contentLayout.addWidget(self.deviceStatusLabel, 0, 2, 1, 2)
        self.contentLayout.addWidget(self.deviceStatus, 1, 2, 4, 2)

        self.contentLayout.setRowStretch(2, 2)

        self.setLayout(self.contentLayout)

        self.deviceList.itemChanged.connect(self.highlightChecked)
        self.reloadData()

    def updateStatus(self, param):
        self.status[param["dev"]] = "{}".format(param["status"])
        idx = 0
        self.deviceStatus.setRowCount(len(self.status))
        for k, v in self.status.items():
            self.deviceStatus.setItem(idx, 0, QTableWidgetItem(k))
            self.deviceStatus.setItem(idx, 1, QTableWidgetItem(v))
            idx += 1

    def getSelectedDevices(self):
        checked_devices = []

        count = 0
        while count < self.deviceList.count():
            item = self.deviceList.item(count)
            if item.checkState() == Qt.Checked:
                checked_devices.append(item.text())
            count += 1

        _devices = []
        for prefix in checked_devices:
            for device in self.devices:
                if device["prefix"] == prefix:
                    _devices.append(device)
                    break
        return _devices

    def highlightChecked(self, item):
        if item.checkState() == Qt.Checked:
            item.setBackground(QColor("#ffffb2"))
        else:
            item.setBackground(QColor("#ffffff"))

    def updateDeviceList(self):
        self.deviceList.clear()

        _filter = self.devicePrefixFilterInp.text()
        devs = []
        for d in self.devices:
            if _filter == "" or _filter in d["prefix"]:
                devs.append(d["prefix"])

        self.deviceList.addItems(devs)

        count = 0
        while count < self.deviceList.count():
            item = self.deviceList.item(count)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            count += 1

    def reloadData(self):
        data = getAgilent()
        self.devices = [d for d in getDevices(data)]
        self.updateDeviceList()


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("VACS - Utility Scripts")

        self.contentLayout = QGridLayout()
        self.content = QFrame()
        self.content.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.content.setLayout(self.contentLayout)

        # to Step Mode
        self.toStepButton = QPushButton("to Step")
        self.toStepButton.setToolTip("Set the voltage behaviour to Step mode.")
        self.toStepButton.clicked.connect(self.toStepAction)
        self.contentLayout.addWidget(self.toStepButton, 0, 0, 1, 1)

        # to Fixed
        self.toFixedButton = QPushButton("to Fixed")
        self.toFixedButton.setToolTip(
            "Set the voltage behaviour to Fixed mode and apply a new voltage setpoint."
        )
        self.toFixedButton.clicked.connect(self.toFixedAction)
        self.contentLayout.addWidget(self.toFixedButton, 1, 0, 1, 1)

        # to Step to Fixed
        self.toStepToFixedButton = QPushButton("to Step delay to Fixed")
        self.toStepToFixedButton.clicked.connect(self.toStepToFixAction)
        self.toStepToFixedButton.setToolTip(
            "Set the behaviour to Step, wait n seconds, set the voltage to Fixed applying a new voltage setpoint."
        )
        self.contentLayout.addWidget(self.toStepToFixedButton, 2, 0, 1, 1)

        # Parameters
        self.parameters = Parameters()
        self.parameters.show()
        self.contentLayout.addWidget(self.parameters, 0, 1, 4, 1)

        # Devices
        self.devices = Devices()
        self.devices.show()
        self.contentLayout.addWidget(self.devices, 5, 0, 1, 2)
        self.content.show()
        self.setCentralWidget(self.content)

        # Thread !
        self.commandRunning = False

    def debug(self, param):
        self.devices.updateStatus(param)

    def enableComponents(self, enable):
        self.devices.updateDeviceListButton.setEnabled(enable)

        self.toStepButton.setEnabled(enable)
        self.toFixedButton.setEnabled(enable)
        self.toStepToFixedButton.setEnabled(enable)

    def started(self):
        self.commandRunning = True
        self.enableComponents(False)

        self.devices.deviceStatus.clearContents()
        self.devices.deviceStatus.setRowCount(0)

    def finished(self):
        self.commandRunning = False
        self.enableComponents(True)

    def toStepAction(self):
        self.doAction(MODE_STEP)

    def toFixedAction(self):
        self.doAction(MODE_FIXED)

    def toStepToFixAction(self):
        self.doAction(MODE_STEP_TO_FIXED)

    def doAction(self, mode):
        if not self.commandRunning:

            agilentAsync = AgilentAsync()
            agilentAsync.timerStatus.connect(self.debug)
            agilentAsync.started.connect(self.started)
            agilentAsync.finished.connect(self.finished)

            runnable = AgilentAsyncRunnable(
                agilentAsync,
                mode=mode,
                voltage=self.parameters.voltage,
                step_to_fixed_delay=self.parameters.delay,
                devices=self.devices.getSelectedDevices(),
            )
            QThreadPool.globalInstance().start(runnable)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d,%H:%M:%S",
    )

    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec_()
