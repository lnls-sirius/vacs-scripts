#!/usr/bin/env python3
from qtpy.QtWidgets import (
    QApplication,
    QWidget,
    QFrame,
    QMainWindow,
    QLabel,
    QPushButton,
    QGridLayout,
    QSpacerItem,
    QSizePolicy,
    QLineEdit,
    QListWidget,
)
from qtpy.QtGui import QRegExpValidator, QIntValidator, QDoubleValidator

from qtpy.QtCore import Qt, QRegExp
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

        self.devicePrefixFilterLabel = QLabel("Device prefix filter")
        self.devicePrefixFilterInp = QLineEdit()

        self.reloadDevicesButton = QPushButton("Reload devices")
        self.reloadDevicesButton.clicked.connect(self.reloadData)

        self.contentLayout.addWidget(self.devicePrefixFilterLabel, 0, 0, 1, 1)
        self.contentLayout.addWidget(self.devicePrefixFilterInp, 0, 1, 1, 1)
        self.contentLayout.addWidget(self.reloadDevicesButton, 0, 2, 1, 1)

        self.deviceList = QListWidget()
        self.contentLayout.addWidget(self.deviceList, 4, 0, 1, 3)
        self.contentLayout.setRowStretch(4, 2)

        self.setLayout(self.contentLayout)

    def updateDeviceList(self):
        self.deviceList.clear()
        # @todo: filter ...
        devs = [d["prefix"] for d in self.devices]
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

        contentLayout = QGridLayout()
        content = QFrame()
        content.setFrameStyle(QFrame.Panel | QFrame.Raised)
        content.setLayout(contentLayout)

        # to Step Mode
        toStepButton = QPushButton("to Step")
        contentLayout.addWidget(toStepButton, 0, 0, 1, 1)

        # to Fixed
        toFixedButton = QPushButton("to Fixed")
        contentLayout.addWidget(toFixedButton, 1, 0, 1, 1)

        # to Step to Fixed
        toFixedButton = QPushButton("to Step delay to Fixed")
        contentLayout.addWidget(toFixedButton, 2, 0, 1, 1)

        # Parameters
        parameters = Parameters()
        parameters.show()
        contentLayout.addWidget(parameters, 0, 1, 4, 1)

        # Prefix filter
        devices = Devices()
        devices.show()
        contentLayout.addWidget(devices, 5, 0, 1, 2)
        content.show()
        self.setCentralWidget(content)


if __name__ == "__main__":
    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec_()
