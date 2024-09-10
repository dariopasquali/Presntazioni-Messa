import sys

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QListWidget

if __name__ == '__main__':
    app = QApplication(sys.argv)
    listWidget = QListWidget()

    listWidget.addItems(["data{}".format(i) for i in range(10)])

    listWidget.setSelectionMode(QListWidget.MultiSelection)
    index = ['data2', 'data3', 'data5']
    for i in index:
        matching_items = listWidget.findItems(i, Qt.MatchExactly)
        for item in matching_items:
            item.setSelected(True)

    listWidget.show()
    sys.exit(app.exec_())