import sys
from datetime import datetime
import calendar
from PyQt5.QtWidgets import QApplication, QWidget, QCalendarWidget, QComboBox
from PyQt5.QtCore import QDate
import os
import PyQt5
import glob
from PyQt5.QtWidgets import QMessageBox

fileSelected = ""


class Calendar(QWidget):
    global currentYear, currentMonth

    currentMonth = datetime.now().month
    currentYear = datetime.now().year

    def __init__(self, location_id, app):
        super().__init__()
        self.location_id = location_id
        self.app = app
        self.setWindowTitle('Open Report for {}'.format(self.location_id))
        self.setGeometry(0, 0, 456, 303)
        self.initUI()

    def initUI(self):
        self.calendar = QCalendarWidget(self)
        self.calendar.setGeometry(0, 0, 451, 297)
        self.calendar.setGridVisible(True)

        self.calendar.setMinimumDate(QDate(currentYear, currentMonth - 1, 1))
        self.calendar.setMaximumDate(
            QDate(currentYear, currentMonth + 1, calendar.monthrange(currentYear, currentMonth)[1]))

        self.calendar.setSelectedDate(QDate(currentYear, currentMonth, 1))
        self.calendar.clicked.connect(self.printDateInfo)

    def printDateInfo(self, qDate):
        if len(str(qDate.month())) < 2:
            month = "0" + str(qDate.month())
        else:
            month = qDate.month()

        if len(str(qDate.day())) < 2:
            day = "0" + str(qDate.day())
        else:
            day = qDate.day()
        directory = (os.path.dirname(os.path.abspath(__file__)) + os.sep + "reports" + os.sep + (
            '{}-{}-{}'.format(qDate.year(), month, day, )))

        today = datetime.now().strftime("%Y-%m-%d")
        selectedDate = '{}-{}-{}'.format(qDate.year(), month, day)

        if selectedDate <= today:
            for file in glob.glob(directory + "/*"):
                if ('{}-{}-{}-{}'.format(qDate.year(), month, day, self.location_id)) in file:
                    global fileSelected
                    fileSelected = file

            if not fileSelected:
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setText("Report for {} Location is not available on {}".format(self.location_id, (
                    '{}-{}-{}'.format(qDate.year(), month, day))))
                msgBox.setWindowTitle("ERROR")
                returnValue = msgBox.exec()
        else:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText('{}-{}-{} is Future date'.format(qDate.year(), month, day))
            msgBox.setWindowTitle("ERROR")
            returnValue = msgBox.exec()

        self.close()


def main():
    app = QApplication(sys.argv)
    location_id = sys.argv[1]
    demo = Calendar(location_id, app)
    demo.show()
    app.exec_()
    return fileSelected


if __name__ == "__main__":
    out = main()
    os.system(out)
