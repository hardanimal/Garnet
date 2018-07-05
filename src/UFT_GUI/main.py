#!/usr/bin/env python
# encoding: utf-8

'''
Created on Nov 01, 2014
@author: mzfa
'''
__author__ = "mzfa"
__version__ = "1.0"
__email__ = "mzfa@cypress.com"

import sys
import logging
import time
from PyQt4.QtGui import QApplication
from PyQt4 import QtGui, QtCore
from UFT_GUI.UFT_UiHandler import UFT_UiHandler
from UFT_GUI import log_handler
from UFT.config import CYCLE_MODE, CYCLE_TIMES, CYCLE_INTERVAL

app = QApplication(sys.argv)
app.setStyle("Plastique")

try:
    import UFT
    from UFT.channel import Channel
except Exception as e:
    msg = QtGui.QMessageBox()
    msg.critical(msg, "error", e.message)
    # msg.exec_()


class MainWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        # self.qtobj = QtCore.QObject()
        self.ui = UFT_UiHandler()
        self.ui.setupUi(self)
        self.ui.setupWidget(self)
        self.__setupSignal()

    def __setupSignal(self):
        """start_pushButton for log display test,
        to be changed as "start" function later
        """

        handler = log_handler.QtHandler()
        handler.setFormatter(UFT.formatter)
        UFT.logger.addHandler(handler)
        UFT.logger.setLevel(logging.INFO)
        log_handler.XStream.stdout().messageWritten.connect(
            self.ui.append_format_data)
        self.ui.start_pushButton.clicked.connect(self.start_click)
        self.ui.partNum_comboBox.currentIndexChanged.connect(
            self.ui.testItem_update)
        self.ui.revision_comboBox.currentIndexChanged.connect(
            self.ui.update_table)
        self.ui.submit_pushButton.clicked.connect(self.ui.submit_config)
        self.ui.search_lineEdit.returnPressed.connect(self.ui.search)
        self.ui.search_pushButton.clicked.connect(self.ui.search)
        self.ui.checkBox.toggled.connect(self.ui.config_edit_toggle)
        self.ui.Mode4in1.toggled.connect(self.ui.switch_between_mode4in1)
        self.ui.tabWidget.currentChanged.connect(self.ui.select_first_slot)

        self.u = Update()

    def start_click(self):
        try:
            mode4in1 = self.ui.InMode4in1()
            # Erie #1
            db_1 = self.ui.barcodes_1()
            cb_1 = self.ui.cabel_barcodes_1()
            bb_1 = self.ui.capacitor_barcodes_1()
            # Erie #2
            db_2 = self.ui.barcodes_2()
            cb_2 = self.ui.cabel_barcodes_2()
            bb_2 = self.ui.capacitor_barcodes_2()
            # Erie #3
            db_3 = self.ui.barcodes_3()
            cb_3 = self.ui.cabel_barcodes_3()
            bb_3 = self.ui.capacitor_barcodes_3()
            # Erie #4
            db_4 = self.ui.barcodes_4()
            cb_4 = self.ui.cabel_barcodes_4()
            bb_4 = self.ui.capacitor_barcodes_4()

            self.u.loaddata(db_1, cb_1, bb_1, db_2, cb_2, bb_2, db_3, cb_3, bb_3, db_4, cb_4, bb_4, mode4in1)
            self.connect(self.u, QtCore.SIGNAL('progress_bar'),
                         self.ui.progressBar.setValue)
            self.connect(self.u, QtCore.SIGNAL('is_alive'),
                         self.ui.auto_enable_disable_widgets)
            self.connect(self.u, QtCore.SIGNAL("dut_status_1"),
                         self.ui.set_dut_status_1)
            self.connect(self.u, QtCore.SIGNAL("dut_status_2"),
                         self.ui.set_dut_status_2)
            self.connect(self.u, QtCore.SIGNAL("dut_status_3"),
                         self.ui.set_dut_status_3)
            self.connect(self.u, QtCore.SIGNAL("dut_status_4"),
                         self.ui.set_dut_status_4)
            self.connect(self.u, QtCore.SIGNAL("board_status_1"),
                         self.ui.set_board_status_1)
            self.connect(self.u, QtCore.SIGNAL("board_status_2"),
                         self.ui.set_board_status_2)
            self.connect(self.u, QtCore.SIGNAL("board_status_3"),
                         self.ui.set_board_status_3)
            self.connect(self.u, QtCore.SIGNAL("board_status_4"),
                         self.ui.set_board_status_4)
            self.connect(self.u, QtCore.SIGNAL('time_used'),
                         self.ui.print_time)
            self.u.start()

        except Exception as e:
            msg = QtGui.QMessageBox()
            msg.critical(self, "error", e.message)
            # msg.show()
            # msg.exec_()


class Update(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)

    def loaddata(self, barcodes_1, cable_barcodes_1, capacitor_barcodes_1,
                 barcodes_2, cable_barcodes_2, capacitor_barcodes_2,
                 barcodes_3, cable_barcodes_3, capacitor_barcodes_3,
                 barcodes_4, cable_barcodes_4, capacitor_barcodes_4,
                 mode):
        # Erie #1
        self.barcodes_1 = barcodes_1
        self.cable_barcodes_1 = cable_barcodes_1
        self.capacitor_barcodes_1 = capacitor_barcodes_1
        # Erie #2
        self.barcodes_2 = barcodes_2
        self.cable_barcodes_2 = cable_barcodes_2
        self.capacitor_barcodes_2 = capacitor_barcodes_2
        # Erie #3
        self.barcodes_3 = barcodes_3
        self.cable_barcodes_3 = cable_barcodes_3
        self.capacitor_barcodes_3 = capacitor_barcodes_3
        # Erie #4
        self.barcodes_4 = barcodes_4
        self.cable_barcodes_4 = cable_barcodes_4
        self.capacitor_barcodes_4 = capacitor_barcodes_4
        self.mode = mode

    def getcurrentprocessbar(self, f_ch1, bar1,
                             f_ch2, bar2,
                             f_ch3, bar3,
                             f_ch4, bar4):
        if not f_ch1:
            bar1 = 100
        if not f_ch2:
            bar2 = 100
        if not f_ch3:
            bar3 = 100
        if not f_ch4:
            bar4 = 100
        return min(bar1, bar2, bar3, bar4)

    def single_run(self):
        sec_count = 0
        ch1 = Channel(barcode_list=self.barcodes_1, cable_barcodes_list=self.cable_barcodes_1, capacitor_barcodes_list=self.capacitor_barcodes_1,
                          channel_id=0, name="UFT_CHANNEL", mode4in1=self.mode)
        ch2 = Channel(barcode_list=self.barcodes_2, cable_barcodes_list=self.cable_barcodes_2, capacitor_barcodes_list=self.capacitor_barcodes_2,
                          channel_id=1, name="UFT_CHANNEL", mode4in1=self.mode)
        ch3 = Channel(barcode_list=self.barcodes_3, cable_barcodes_list=self.cable_barcodes_3, capacitor_barcodes_list=self.capacitor_barcodes_3,
                          channel_id=2, name="UFT_CHANNEL", mode4in1=self.mode)
        ch4 = Channel(barcode_list=self.barcodes_4, cable_barcodes_list=self.cable_barcodes_4, capacitor_barcodes_list=self.capacitor_barcodes_4,
                          channel_id=3, name="UFT_CHANNEL", mode4in1=self.mode)
        ch1.auto_test()
        ch2.auto_test()
        ch3.auto_test()
        ch4.auto_test()
        self.emit(QtCore.SIGNAL("is_alive"), 1)
        while ch1.isAlive() or ch2.isAlive() or ch3.isAlive() or ch4.isAlive():
            sec_count += 1
            c_process = self.getcurrentprocessbar(ch1.isAlive(), ch1.progressbar,
                                                  ch2.isAlive(), ch2.progressbar,
                                                  ch3.isAlive(), ch3.progressbar,
                                                  ch4.isAlive(), ch4.progressbar)
            self.emit(QtCore.SIGNAL("progress_bar"), c_process)
            self.emit(QtCore.SIGNAL("time_used"), sec_count)
            for dut in ch1.dut_list:
                if dut is not None:
                    self.emit(QtCore.SIGNAL("dut_status_1"), dut.slotnum,
                              dut.status)
            for dut in ch2.dut_list:
                if dut is not None:
                    self.emit(QtCore.SIGNAL("dut_status_2"), dut.slotnum,
                              dut.status)
            for dut in ch3.dut_list:
                if dut is not None:
                    self.emit(QtCore.SIGNAL("dut_status_3"), dut.slotnum,
                              dut.status)
            for dut in ch4.dut_list:
                if dut is not None:
                    self.emit(QtCore.SIGNAL("dut_status_4"), dut.slotnum,
                              dut.status)
            self.emit(QtCore.SIGNAL("board_status_1"), ch1.channelresult)
            self.emit(QtCore.SIGNAL("board_status_2"), ch2.channelresult)
            self.emit(QtCore.SIGNAL("board_status_3"), ch3.channelresult)
            self.emit(QtCore.SIGNAL("board_status_4"), ch4.channelresult)
            time.sleep(1)

        self.emit(QtCore.SIGNAL("progress_bar"), 100)
        for dut in ch1.dut_list:
            if dut is not None:
                self.emit(QtCore.SIGNAL("dut_status_1"), dut.slotnum, dut.status)
        for dut in ch2.dut_list:
            if dut is not None:
                self.emit(QtCore.SIGNAL("dut_status_2"), dut.slotnum, dut.status)
        for dut in ch3.dut_list:
            if dut is not None:
                self.emit(QtCore.SIGNAL("dut_status_3"), dut.slotnum, dut.status)
        for dut in ch4.dut_list:
            if dut is not None:
                self.emit(QtCore.SIGNAL("dut_status_4"), dut.slotnum, dut.status)
        self.emit(QtCore.SIGNAL("board_status_1"), ch1.channelresult)
        self.emit(QtCore.SIGNAL("board_status_2"), ch2.channelresult)
        self.emit(QtCore.SIGNAL("board_status_3"), ch3.channelresult)
        self.emit(QtCore.SIGNAL("board_status_4"), ch4.channelresult)

        # clean resource
        if ch1 is not None:
            ch1.save_db()
            time.sleep(0.5)
            del ch1
        if ch2 is not None:
            ch2.save_db()
            time.sleep(0.5)
            del ch2
        if ch3 is not None:
            ch3.save_db()
            time.sleep(0.5)
            del ch3
        if ch4 is not None:
            ch4.save_db()
            time.sleep(0.5)
            del ch4
        #self.terminate()
        self.emit(QtCore.SIGNAL("is_alive"), 0)

    def run(self):
        if CYCLE_MODE:
            for i in range(0, CYCLE_TIMES):
                self.single_run()
                time.sleep(CYCLE_INTERVAL)
        else:
            self.single_run()


def main():
    # app = QApplication(sys.argv)
    # app.setStyle("Plastique")
    widget = MainWidget()
    widget.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
