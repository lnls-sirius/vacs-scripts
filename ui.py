#!/usr/bin/env python3
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
    QWidget,
)
from qtpy.QtGui import QRegExpValidator, QIntValidator, QDoubleValidator, QColor

from qtpy.QtCore import Qt, QRegExp, QObject
from utils import getDevices, getAgilent


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
        self.setpointVoltageInp.setValidator(QIntValidator(3000, 7000))

        self.contentLayout.addWidget(self.setpointVoltageLabel, 0, 0, 1, 1)
        self.contentLayout.addWidget(self.setpointVoltageInp, 0, 1, 1, 1)
        self.contentLayout.addWidget(self.setpointVoltageSettingLabel, 0, 2, 1, 1)

        self.stepToFixDelayLabel = QLabel("Step to Fixed delay in seconds")
        self.stepToFixDelaySettingLabel = QLabel()
        self.stepToFixDelayInp = QLineEdit()
        self.stepToFixDelayInp.setValidator(QDoubleValidator(1, 1440, 2))

        self.contentLayout.addWidget(self.stepToFixDelayLabel, 1, 0, 1, 1)
        self.contentLayout.addWidget(self.stepToFixDelayInp, 1, 1, 1, 1)
        self.contentLayout.addWidget(self.stepToFixDelaySettingLabel, 1, 2, 1, 1)

        self.setButton = QPushButton("Confirm")
        self.setButton.clicked.connect(self.confirm)
        self.contentLayout.addWidget(self.setButton, 3, 1, 1, 1)

        self.setLayout(self.contentLayout)
        self.confirm()

    def confirm(self):
        try:
            voltageString = self.setpointVoltageInp.text()
            tmp = int(voltageString)
            self.voltage = 3000 if tmp < 3000 else (7000 if tmp > 7000 else tmp)

            delayString = self.stepToFixDelayInp.text()
            tmp = float(delayString)
            self.delay = 1.0 if tmp < 1.0 else (1440.0 if tmp > 1440.0 else tmp)
        except ValueError:
            pass
        finally:
            self.setpointVoltageSettingLabel.setText("{}".format(self.voltage))
            self.stepToFixDelaySettingLabel.setText("{}".format(self.delay))


class Devices(QFrame):
    def __init__(self, *args, **kwargs):
        super(Devices, self).__init__(*args, **kwargs)
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.contentLayout = QGridLayout()

        self.devices = []

        self.devicePrefixFilterLabel = QLabel(
            "Device filter (Ion Pump not the channel!)"
        )
        self.devicePrefixFilterInp = QLineEdit()

        self.updateDeviceListButton = QPushButton("Update devices list")
        self.updateDeviceListButton.clicked.connect(self.updateDeviceList)

        self.reloadDevicesButton = QPushButton("Reload devices")
        self.reloadDevicesButton.clicked.connect(self.reloadData)

        self.contentLayout.addWidget(self.devicePrefixFilterLabel, 0, 0, 1, 1)
        self.contentLayout.addWidget(self.devicePrefixFilterInp, 0, 1, 1, 1)
        self.contentLayout.addWidget(self.updateDeviceListButton, 0, 2, 1, 1)
        self.contentLayout.addWidget(self.reloadDevicesButton, 0, 3, 1, 1)

        self.deviceList = QListWidget()
        self.contentLayout.addWidget(self.deviceList, 4, 0, 1, 4)
        self.contentLayout.setRowStretch(4, 2)

        self.setLayout(self.contentLayout)

        self.deviceList.itemChanged.connect(self.highlightChecked)
        self.reloadData()

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
        self.contentLayout.addWidget(self.toStepButton, 0, 0, 1, 1)

        # to Fixed
        self.toFixedButton = QPushButton("to Fixed")
        self.contentLayout.addWidget(self.toFixedButton, 1, 0, 1, 1)

        # to Step to Fixed
        self.toStepToFixedButton = QPushButton("to Step delay to Fixed")
        self.contentLayout.addWidget(self.toStepToFixedButton, 2, 0, 1, 1)
        self.toStepToFixedButton.clicked.connect(self.toStepToFixAction)

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

    def toStepToFixAction(self):
        print(self.devices.getSelectedDevices())


if __name__ == "__main__":
    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec_()
