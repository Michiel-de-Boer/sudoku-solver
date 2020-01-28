#!/usr/bin/env python
import sys
import time
import re
import ctypes
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon, QIntValidator, QRegExpValidator, QColor
from PyQt5.QtCore import Qt, QObject, QRegExp, QThread
from PyQt5.QtWidgets import QTableWidget, QLineEdit, QItemDelegate, QTableWidgetItem
from PyQt5 import uic
import sudoku_solver


def set_tbl_wgt_item(w, row, col, var):
    # if not var: var = ''
    var = var or ''
    w.item(row, col).setText(str(var))


def init_tbl_items(table_widget):
    for row in range(9):
        for col in range(9):
            item = QTableWidgetItem('')
            item.setTextAlignment(int(Qt.AlignHCenter | Qt.AlignVCenter))
            table_widget.setItem(row, col, item)
            blk_num = ((row // 3) * 3) + (col // 3)
            # 1 = top middle, 3 = middle left, 5 = middle right, 7 = bottom middle
            if blk_num in (1, 3, 5, 7):
                table_widget.item(row, col).setBackground(QColor(240, 246, 232))
            else:
                table_widget.item(row, col).setBackground(QColor(255, 255, 255))


def populate_2d_arr_from_wgt(table_widget):
    grid = []
    for row_ind in range(9):
        row = []
        for col_ind in range(9):
            var = table_widget.item(row_ind, col_ind).text()
            if var == '': var = 0
            else: var = int(var)
            row.append(var)
        grid.append(row)
    return grid


def populate_wgt_from_2d_arr(widget, arr, highlight = False):
    for row in range(9):
        for col in range(9):
            # var = arr[row, col] or ''
            var = arr[row][col] or ''
            if highlight and widget.item(row, col).text() == '':
                    widget.item(row, col).setForeground(QColor(125, 130, 130))
            widget.item(row, col).setText(str(var))


class Table(QTableWidget):
    def __init__(self):
        super(QTableWidget, self).__init__()

    def paintEvent(self, event):
        pass


class WorkerThread(QObject):
    signal_finished = QtCore.pyqtSignal(object)
    signal_update = QtCore.pyqtSignal(object)

    def __init__(self, grid):
        super().__init__()
        self.grid = grid

    def callback(self, response):
        self.signal_update.emit(response)
        # time.sleep(3)

    @QtCore.pyqtSlot()
    def run(self):
        self._active = True
        try:
            # sudoku_solver = Solver
            solver = suduko_solver.Solver(self.grid)
            response = solver.solve(max_loops=1000, callback=self.callback)
            # response = solver.solve_backtrack()
        except InterruptedError:
            pass
        finally:
            self._active = False
            self.signal_finished.emit(response)


class Validate(QItemDelegate):
    def createEditor(self, parent, option, ind):
        le = QLineEdit(parent)
        # vd = QIntValidator(1, 9, le)
        vd = QRegExpValidator(QRegExp("[1-9]|^$"))
        le.setValidator(vd)
        return le


class Ui(QtWidgets.QMainWindow):
    def eventFilter(self, source, event):
        if source is self.tblSud and event.type() == QtCore.QEvent.KeyPress:
            row, col = self.tblSud.currentRow(), self.tblSud.currentColumn()
            if re.match('[1-9]', event.text()):
                input = event.text()
                # print('Number: "%s"' % input)
                self.tblSud.item(row, col).setText(input)
                return True
            elif event.key() == Qt.Key_Delete:
                self.tblSud.item(row, col).setText('')
                # print(event.key(), '"%s"' % event.text())
        return super(Ui, self).eventFilter(source, event)

    def signal_finished(self, response):
        self.btnGo.setEnabled(True)
        if response.solved:
            populate_wgt_from_2d_arr(self.tblSud, response.result, highlight=True)
        else:
            print(response.error, response.loop_count)
            print(response.result)

    def signal_update(self, response):
            populate_wgt_from_2d_arr(self.tblSud, response.result, highlight=True)

    def btn_go(self):
        self.btnGo.setEnabled(False)

        grid = populate_2d_arr_from_wgt(self.tblSud)

        self.worker = WorkerThread(grid)
        try:
            # Put a try here because clean-up of previous run may have failed.
            # This is a fugly workaround.
            self.worker_thread = QThread()
        except:
            self.worker_thread.quit()
            self.worker_thread = QThread()

        self.worker_thread.started.connect(self.worker.run)
        self.worker.signal_finished.connect(self.signal_finished)
        self.worker.signal_update.connect(self.signal_update)

        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()
        # print("Number of runs: %i" % int(maxloops + 1))

    def __init__(self):
        # super(Ui, self).__init__()
        super().__init__()
        uic.loadUi('main.ui', self)

        self.btnGo.clicked.connect(self.btn_go)
        '''
        # Easy
        tmpl_sud = (
            (0, 2, 0, 7, 0, 4, 3, 0, 8),
            (0, 0, 0, 0, 9, 6, 0, 0, 0),
            (0, 0, 7, 8, 0, 2, 6, 0, 0),
            (0, 8, 9, 0, 2, 1, 0, 0, 4),
            (0, 0, 0, 0, 0, 0, 0, 0, 0),
            (0, 0, 0, 3, 0, 0, 0, 0, 0),
            (0, 0, 0, 0, 0, 0, 8, 0, 5),
            (5, 0, 0, 9, 0, 7, 0, 4, 0),
            (0, 0, 0, 0, 5, 0, 1, 6, 7)
        )
        '''

        tmpl_sud = (
            (0, 0, 8, 9, 0, 0, 5, 0, 0),
            (2, 0, 0, 1, 0, 4, 0, 0, 6),
            (0, 9, 0, 0, 7, 5, 0, 0, 0),
            (0, 0, 0, 5, 0, 0, 2, 0, 0),
            (0, 5, 6, 0, 0, 1, 4, 0, 0),
            (0, 0, 0, 4, 0, 0, 0, 0, 1),
            (0, 0, 0, 0, 0, 0, 0, 0, 9),
            (1, 8, 0, 2, 0, 0, 6, 0, 0),
            (5, 2, 0, 0, 0, 0, 0, 0, 3)
        )

        tmpl_sud = (
            (8, 9, 0, 1, 0, 0, 0, 7, 0),
            (0, 5, 0, 0, 7, 3, 8, 1, 0),
            (7, 0, 0, 8, 4, 0, 0, 5, 0),
            (0, 0, 3, 0, 0, 0, 4, 0, 1),
            (5, 0, 0, 0, 0, 6, 0, 0, 0),
            (0, 0, 0, 4, 3, 0, 0, 0, 0),
            (0, 0, 0, 6, 5, 0, 0, 0, 0),
            (0, 0, 0, 0, 1, 0, 0, 0, 5),
            (0, 0, 0, 0, 0, 7, 0, 0, 3)
        )

        init_tbl_items(self.tblSud)

        # populate_wgt_from_2d_arr(self.tblSud, tmpl_sud)

        self.tblSud.setItemDelegate(Validate(self.tblSud))
        self.tblSud.installEventFilter(self)

        self.show()


# PyQt suppresses exceptions. I'd rather not have that. So attempt to stop it from happening.
def catch_exceptions(t, val, tb):
    # QtWidgets.QMessageBox.critical(None, "An exception was raised", "Exception type: {}".format(t))
    print("Exception: %s %s %s" % (t, val, tb))
    old_hook(t, val, tb)


# PyQt suppresses exceptions. I'd rather not have that. So attempt to stop it from happening.
# So far, with mixed success.
old_hook = sys.excepthook
sys.excepthook = catch_exceptions

# Necessary to tell Windows this app is its own, to prevent taskbar icon set to icon of pythonw.exe
# See https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105#1552105
myappid = 'Sudoku Solver' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()

# TODO: stop button, clear button, clear solution button, save state, check if sudoku valid