#!/usr/bin/env python3
import sys
from utils import getAgilent, getDevices
from collections import deque
from qtpy import QtCore, QtGui, QtWidgets


class Window(QtWidgets.QWidget):
    def __init__(self, data):
        super(Window, self).__init__()

        self.tree = QtWidgets.QTreeView(self)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.tree)

        self.model = QtGui.QStandardItemModel()
        self.model.dataChanged.connect(self.itemChanged)

        self.tree.header().setDefaultSectionSize(180)
        self.tree.setModel(self.model)
        self.model.itemChanged.connect(self.itemChanged)

        self.importData(data)
        self.tree.expandAll()

        self.button = QtWidgets.QPushButton("Get")
        self.button.clicked.connect(self.getData)
        layout.addWidget(self.button)

    def importData(self, data, root=None):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["", ""])
        self.model.setRowCount(0)

        count = 0
        if root is None:
            root = self.model.invisibleRootItem()

        for d in data:
            item_dev = QtGui.QStandardItem(d["prefix"])
            item_dev.setAutoTristate(False)
            item_dev.setCheckable(True)
            item_dev.setEditable(False)
            item_dev.setUserTristate(False)

            for ch_n, ch in d["channels"].items():
                i_ = QtGui.QStandardItem(ch_n)
                i_.setAutoTristate(False)
                i_.setCheckable(True)
                i_.setEditable(False)
                i_.setUserTristate(False)

                i_p = QtGui.QStandardItem(ch["prefix"])
                i_p.setEditable(False)

                item_dev.appendRow([i_, i_p])

            root.appendRow(item_dev)
            count += 1
        self.model.setRowCount(count)

    def checkParentState(self, item):
        checked = 0
        for row in range(item.rowCount()):
            if item.child(row, 0).checkState() != 0:
                checked += 1

        if checked == item.rowCount():
            return 2
        elif checked == 0:
            return 0
        else:
            return 1

    def getDevices(self):
        checked = self.model.match(
            self.model.index(0, 0),
            QtCore.Qt.CheckStateRole,
            1,
            -1,
            QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive,
        )
        for index in checked:
            item = self.model.itemFromIndex(index)
            print(item.text())

    def getData(self):
        root = self.model.invisibleRootItem()
        selected = {}
        for i in range(root.rowCount()):
            row = root.child(i, 0)

            if row.isCheckable() and row.checkState() != 0:
                channels = {}
                for j in range(row.rowCount()):
                    if row.child(j, 0).checkState() != 0:
                        channels[row.child(j, 0).text()] = {
                            "prefix": row.child(j, 1).text()
                        }
                selected[row.text()] = {"channels": channels}
        print(selected)
        return selected

    def itemChanged(self, item):

        if type(item) == QtGui.QStandardItem:
            parent = item.parent()

            if item.rowCount() > 0 and parent is None:
                pass  # if item.checkState() == 0 or item.checkState() == 2:
                # for row in range(item.rowCount()):
                #    if item.child(row, 0).checkState() != item.checkState():
                #        item.child(row, 0).setCheckState(item.checkState())
                # if item.checkState() == 0 or item.checkState() == 2:
                #    for row in range(item.rowCount()):
                #        if item.child(row, 0).checkState() != item.checkState():
                #            item.child(row, 0).setCheckState(item.checkState())
            else:
                # A device ...
                if parent and parent.isCheckable():
                    state = self.checkParentState(parent)
                    parent.setCheckState(state)

            if item.isCheckable():
                if item.checkState() == 0:
                    item.setBackground(QtGui.QColor("#fffff2"))
                elif item.checkState() == 1:
                    item.setBackground(QtGui.QColor("#ffffb2"))
                elif item.checkState() == 2:
                    item.setBackground(QtGui.QColor("#c0ffb2"))


if __name__ == "__main__":

    data = getDevices(getAgilent())

    app = QtWidgets.QApplication(sys.argv)
    window = Window(data)
    window.setGeometry(600, 50, 400, 250)
    window.show()
    sys.exit(app.exec_())
