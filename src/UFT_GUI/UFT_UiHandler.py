#!/usr/bin/env python
# encoding: utf-8

'''
Created on Nov 01, 2014
@author: mzfa
'''
import sys
import os
import re
from PyQt4 import QtCore, QtGui, QtSql
from UFT_GUI.UFT_Ui import Ui_Form as UFT_UiForm
from UFT.config import RESULT_DB, CONFIG_DB, RESOURCE, CONFIG_FILE, CYCLE_MODE
from UFT.backend import sync_config

BARCODE_PATTERN = re.compile(r'^(?P<SN>(?P<PN>AGIGA\d{4}-\d{3}\w{3})'
                             r'(?P<VV>\d{2})(?P<YY>[1-2][0-9])'
                             r'(?P<WW>[0-4][0-9]|5[0-3])'
                             r'(?P<ID>\d{8})-(?P<RR>\d{2}))$')


# class MyLineEdit(QtGui.QLineEdit):
# def __init__(self, parent=None):
#         super(MyLineEdit, self).__init__(parent)
#
#     def focusInEvent(self, event):
#         # print 'This widget is in focus'
#         self.clear()
#         QtGui.QLineEdit.focusInEvent(self,
#                                      QtGui.QFocusEvent(QtCore.QEvent.FocusIn))


class LoginDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle(u'login')
        self.resize(300, 150)

        self.leName = QtGui.QLineEdit(self)
        self.leName.setPlaceholderText(u'user')

        self.lePassword = QtGui.QLineEdit(self)
        self.lePassword.setEchoMode(QtGui.QLineEdit.Password)
        self.lePassword.setPlaceholderText(u'password')

        self.pbLogin = QtGui.QPushButton(u'login', self)
        self.pbCancel = QtGui.QPushButton(u'cancel', self)

        self.pbLogin.clicked.connect(self.login)
        self.pbCancel.clicked.connect(self.reject)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.leName)
        layout.addWidget(self.lePassword)

        spacerItem = QtGui.QSpacerItem(20, 48, QtGui.QSizePolicy.Minimum,
                                       QtGui.QSizePolicy.Expanding)
        layout.addItem(spacerItem)

        buttonLayout = QtGui.QHBoxLayout()
        spancerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding,
                                         QtGui.QSizePolicy.Minimum)
        buttonLayout.addItem(spancerItem2)
        buttonLayout.addWidget(self.pbLogin)
        buttonLayout.addWidget(self.pbCancel)

        layout.addLayout(buttonLayout)

        self.setLayout(layout)

    def login(self):
        print 'login'
        if self.leName.text() == 'cypress' and self.lePassword.text() == '123':
            self.accept()
        else:
            QtGui.QMessageBox.critical(self, u'error', u'password wrong')


class UFT_UiHandler(UFT_UiForm):
    def __init__(self, parent=None):
        UFT_UiForm.__init__(self)
        self.dut_image = None
        # sync config db from config xml
        sync_config("sqlite:///" + CONFIG_DB, CONFIG_FILE, direction="in")
        #
        # setup config db, view and model
        self.config_db = QtSql.QSqlDatabase.addDatabase("QSQLITE", "config")
        self.config_db.setDatabaseName(CONFIG_DB)
        result = self.config_db.open()
        if (not result):
            msgbox = QtGui.QMessageBox()
            msg = self.config_db.lastError().text()
            msgbox.critical(msgbox, "error", msg + " db=" + CONFIG_DB)
        self.config_tableView = QtGui.QTableView()
        # self.test_item_tableView already created in UI.
        self.config_model = QtSql.QSqlTableModel(db=self.config_db)
        self.test_item_model = QtSql.QSqlRelationalTableModel(db=self.config_db)
        self.test_item_model.setEditStrategy(
            QtSql.QSqlTableModel.OnManualSubmit)

        # setup log db, view and model
        self.log_db = QtSql.QSqlDatabase.addDatabase("QSQLITE", "log")
        self.log_db.setDatabaseName(RESULT_DB)
        result = self.log_db.open()
        if (not result):
            msgbox = QtGui.QMessageBox()
            msg = self.config_db.lastError().text()
            msgbox.critical(msgbox, "error", msg + " db=" + RESULT_DB)
        # self.log_tableView
        self.log_model = QtSql.QSqlTableModel(db=self.log_db)
        self.cycle_model = QtSql.QSqlRelationalTableModel(db=self.log_db)

    def setupWidget(self, wobj):
        wobj.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(RESOURCE + "logo.png")))

        # setup configuration model
        self.config_model.setTable("configuration")
        self.test_item_model.setTable("test_item")
        self.test_item_model.setRelation(1, QtSql.QSqlRelation(
            "configuration", "id", u"partnumber"))

        # setup log model
        self.log_model.setTable("dut")
        self.cycle_model.setTable("cycle")
        self.cycle_model.setRelation(7, QtSql.QSqlRelation(
            "dut", "id", u"barcode, archived"))

        # set log view
        self.log_tableView.setModel(self.log_model)
        # self.log_tableView.resizeColumnsToContents()

        # update comboBox
        partnumber_list = []
        self.config_model.select()  # get data
        for row in range(self.config_model.rowCount()):
            index = self.config_model.index(row, 1)  # 1 for partnumber
            pn = self.config_model.data(index).toString()
            if (pn not in partnumber_list):
                partnumber_list.append(pn)
                self.partNum_comboBox.addItem(pn)

        # set configuration view
        self.revision_comboBox.setModel(self.config_model)
        self.revision_comboBox.setModelColumn(self.config_model.fieldIndex(
            "revision"))
        self.test_item_tableView.setModel(self.test_item_model)
        self.testItem_update()

    def auto_enable_disable_widgets(self, ch_is_alive):
        if ch_is_alive:
            self.start_pushButton.setDisabled(True)
            self.Mode4in1.setDisabled(True)
            self.tab_EB1.setDisabled(True)
            self.tab_EB2.setDisabled(True)
            self.tab_EB3.setDisabled(True)
            self.tab_EB4.setDisabled(True)
        else:
            self.start_pushButton.setEnabled(True)
            self.Mode4in1.setEnabled(True)
            self.tab_EB1.setEnabled(True)
            self.tab_EB2.setEnabled(True)
            self.tab_EB3.setEnabled(True)
            self.tab_EB4.setEnabled(True)

            # back to first
            self.sn_lineEdit_1_1.setFocus()
            self.sn_lineEdit_1_1.selectAll()

    def select_first_slot(self, bdid):
        if bdid == 0:
            self.sn_lineEdit_1_1.setFocus()
            self.sn_lineEdit_1_1.selectAll()
            self.label_boardnum.setText("1")
        elif bdid == 1:
            self.sn_lineEdit_2_1.setFocus()
            self.sn_lineEdit_2_1.selectAll()
            self.label_boardnum.setText("2")
        elif bdid == 2:
            self.sn_lineEdit_3_1.setFocus()
            self.sn_lineEdit_3_1.selectAll()
            self.label_boardnum.setText("3")
        elif bdid == 3:
            self.sn_lineEdit_4_1.setFocus()
            self.sn_lineEdit_4_1.selectAll()
            self.label_boardnum.setText("4")
        elif bdid == 6:
            self.search_lineEdit.setFocus()
            self.search_lineEdit.selectAll()
            self.label_boardnum.setText("N")
        else:
            self.label_boardnum.setText("N")

    def append_format_data(self, data):
        if data:
            self.info_textBrowser.append(data)
            # self.info_textBrowser.moveCursor(QtGui.QTextCursor.End)
        else:
            pass

    def clean_pass_sn(self, dut, cable, battery, slotnum, status):
        if not CYCLE_MODE:
            if status == 1:
                dut[slotnum].clear()
                cable[slotnum].clear()
                battery[slotnum].clear()

    def set_label(self, label, slotnum, status):
        status_list = ["Idle", "Pass", "Fail", "Charging", "Discharging", "Self_Discharging",
                       "Cap_Measuring", "Program_VPD", "Running..."]
        color_list = ["background-color: wheat",
                      "background-color: green",
                      "background-color: red",
                      "background-color: yellow",
                      "background-color: yellow",
                      "background-color: yellow",
                      "background-color: yellow",
                      "background-color: yellow",
                      "background-color: yellow"]
        label[slotnum].setText(status_list[status])
        label[slotnum].setStyleSheet(color_list[status])

    def set_dut_status_1(self, slotnum, status):
        label = [self.label_1_1, self.label_1_2, self.label_1_3, self.label_1_4, self.label_1_5, self.label_1_6, self.label_1_7, self.label_1_8,
                 self.label_1_9, self.label_1_10, self.label_1_11, self.label_1_12, self.label_1_13, self.label_1_14, self.label_1_15, self.label_1_16]
        dut = [self.sn_lineEdit_1_1, self.sn_lineEdit_1_2, self.sn_lineEdit_1_3, self.sn_lineEdit_1_4, self.sn_lineEdit_1_5, self.sn_lineEdit_1_6, self.sn_lineEdit_1_7, self.sn_lineEdit_1_8,
               self.sn_lineEdit_1_9, self.sn_lineEdit_1_10, self.sn_lineEdit_1_11, self.sn_lineEdit_1_12, self.sn_lineEdit_1_13, self.sn_lineEdit_1_14, self.sn_lineEdit_1_15, self.sn_lineEdit_1_16]
        cable = [self.CablelineEdit_1_1, self.CablelineEdit_1_2, self.CablelineEdit_1_3, self.CablelineEdit_1_4, self.CablelineEdit_1_5, self.CablelineEdit_1_6, self.CablelineEdit_1_7, self.CablelineEdit_1_8,
                 self.CablelineEdit_1_9, self.CablelineEdit_1_10, self.CablelineEdit_1_11, self.CablelineEdit_1_12, self.CablelineEdit_1_13, self.CablelineEdit_1_14, self.CablelineEdit_1_15, self.CablelineEdit_1_16]
        battery = [self.BatterylineEdit_1_1, self.BatterylineEdit_1_2, self.BatterylineEdit_1_3, self.BatterylineEdit_1_4, self.BatterylineEdit_1_5, self.BatterylineEdit_1_6, self.BatterylineEdit_1_7, self.BatterylineEdit_1_8,
                   self.BatterylineEdit_1_9, self.BatterylineEdit_1_10, self.BatterylineEdit_1_11, self.BatterylineEdit_1_12, self.BatterylineEdit_1_13, self.BatterylineEdit_1_14, self.BatterylineEdit_1_15, self.BatterylineEdit_1_16]
        self.set_label(label, slotnum, status)
        self.clean_pass_sn(dut, cable, battery, slotnum, status)

    def set_dut_status_2(self, slotnum, status):
        label = [self.label_2_1, self.label_2_2, self.label_2_3, self.label_2_4, self.label_2_5, self.label_2_6, self.label_2_7, self.label_2_8,
                 self.label_2_9, self.label_2_10, self.label_2_11, self.label_2_12, self.label_2_13, self.label_2_14, self.label_2_15, self.label_2_16]
        dut = [self.sn_lineEdit_2_1, self.sn_lineEdit_2_2, self.sn_lineEdit_2_3, self.sn_lineEdit_2_4, self.sn_lineEdit_2_5, self.sn_lineEdit_2_6, self.sn_lineEdit_2_7, self.sn_lineEdit_2_8,
               self.sn_lineEdit_2_9, self.sn_lineEdit_2_10, self.sn_lineEdit_2_11, self.sn_lineEdit_2_12, self.sn_lineEdit_2_13, self.sn_lineEdit_2_14, self.sn_lineEdit_2_15, self.sn_lineEdit_2_16]
        cable = [self.CablelineEdit_2_1, self.CablelineEdit_2_2, self.CablelineEdit_2_3, self.CablelineEdit_2_4, self.CablelineEdit_2_5, self.CablelineEdit_2_6, self.CablelineEdit_2_7, self.CablelineEdit_2_8,
                 self.CablelineEdit_2_9, self.CablelineEdit_2_10, self.CablelineEdit_2_11, self.CablelineEdit_2_12, self.CablelineEdit_2_13, self.CablelineEdit_2_14, self.CablelineEdit_2_15, self.CablelineEdit_2_16]
        battery = [self.BatterylineEdit_2_1, self.BatterylineEdit_2_2, self.BatterylineEdit_2_3, self.BatterylineEdit_2_4, self.BatterylineEdit_2_5, self.BatterylineEdit_2_6, self.BatterylineEdit_2_7, self.BatterylineEdit_2_8,
                   self.BatterylineEdit_2_9, self.BatterylineEdit_2_10, self.BatterylineEdit_2_11, self.BatterylineEdit_2_12, self.BatterylineEdit_2_13, self.BatterylineEdit_2_14, self.BatterylineEdit_2_15, self.BatterylineEdit_2_16]
        self.set_label(label, slotnum, status)
        self.clean_pass_sn(dut, cable, battery, slotnum, status)

    def set_dut_status_3(self, slotnum, status):
        label = [self.label_3_1, self.label_3_2, self.label_3_3, self.label_3_4, self.label_3_5, self.label_3_6, self.label_3_7, self.label_3_8,
                 self.label_3_9, self.label_3_10, self.label_3_11, self.label_3_12, self.label_3_13, self.label_3_14, self.label_3_15, self.label_3_16]
        dut = [self.sn_lineEdit_3_1, self.sn_lineEdit_3_2, self.sn_lineEdit_3_3, self.sn_lineEdit_3_4, self.sn_lineEdit_3_5, self.sn_lineEdit_3_6, self.sn_lineEdit_3_7, self.sn_lineEdit_3_8,
               self.sn_lineEdit_3_9, self.sn_lineEdit_3_10, self.sn_lineEdit_3_11, self.sn_lineEdit_3_12, self.sn_lineEdit_3_13, self.sn_lineEdit_3_14, self.sn_lineEdit_3_15, self.sn_lineEdit_3_16]
        cable = [self.CablelineEdit_3_1, self.CablelineEdit_3_2, self.CablelineEdit_3_3, self.CablelineEdit_3_4, self.CablelineEdit_3_5, self.CablelineEdit_3_6, self.CablelineEdit_3_7, self.CablelineEdit_3_8,
                 self.CablelineEdit_3_9, self.CablelineEdit_3_10, self.CablelineEdit_3_11, self.CablelineEdit_3_12, self.CablelineEdit_3_13, self.CablelineEdit_3_14, self.CablelineEdit_3_15, self.CablelineEdit_3_16]
        battery = [self.BatterylineEdit_3_1, self.BatterylineEdit_3_2, self.BatterylineEdit_3_3, self.BatterylineEdit_3_4, self.BatterylineEdit_3_5, self.BatterylineEdit_3_6, self.BatterylineEdit_3_7, self.BatterylineEdit_3_8,
                   self.BatterylineEdit_3_9, self.BatterylineEdit_3_10, self.BatterylineEdit_3_11, self.BatterylineEdit_3_12, self.BatterylineEdit_3_13, self.BatterylineEdit_3_14, self.BatterylineEdit_3_15, self.BatterylineEdit_3_16]
        self.set_label(label, slotnum, status)
        self.clean_pass_sn(dut, cable, battery, slotnum, status)

    def set_dut_status_4(self, slotnum, status):
        label = [self.label_4_1, self.label_4_2, self.label_4_3, self.label_4_4, self.label_4_5, self.label_4_6, self.label_4_7, self.label_4_8,
                 self.label_4_9, self.label_4_10, self.label_4_11, self.label_4_12, self.label_4_13, self.label_4_14, self.label_4_15, self.label_4_16]
        dut = [self.sn_lineEdit_4_1, self.sn_lineEdit_4_2, self.sn_lineEdit_4_3, self.sn_lineEdit_4_4, self.sn_lineEdit_4_5, self.sn_lineEdit_4_6, self.sn_lineEdit_4_7, self.sn_lineEdit_4_8,
               self.sn_lineEdit_4_9, self.sn_lineEdit_4_10, self.sn_lineEdit_4_11, self.sn_lineEdit_4_12, self.sn_lineEdit_4_13, self.sn_lineEdit_4_14, self.sn_lineEdit_4_15, self.sn_lineEdit_4_16]
        cable = [self.CablelineEdit_4_1, self.CablelineEdit_4_2, self.CablelineEdit_4_3, self.CablelineEdit_4_4, self.CablelineEdit_4_5, self.CablelineEdit_4_6, self.CablelineEdit_4_7, self.CablelineEdit_4_8,
                 self.CablelineEdit_4_9, self.CablelineEdit_4_10, self.CablelineEdit_4_11, self.CablelineEdit_4_12, self.CablelineEdit_4_13, self.CablelineEdit_4_14, self.CablelineEdit_4_15, self.CablelineEdit_4_16]
        battery = [self.BatterylineEdit_4_1, self.BatterylineEdit_4_2, self.BatterylineEdit_4_3, self.BatterylineEdit_4_4, self.BatterylineEdit_4_5, self.BatterylineEdit_4_6, self.BatterylineEdit_4_7, self.BatterylineEdit_4_8,
                   self.BatterylineEdit_4_9, self.BatterylineEdit_4_10, self.BatterylineEdit_4_11, self.BatterylineEdit_4_12, self.BatterylineEdit_4_13, self.BatterylineEdit_4_14, self.BatterylineEdit_4_15, self.BatterylineEdit_4_16]
        self.set_label(label, slotnum, status)
        self.clean_pass_sn(dut, cable, battery, slotnum, status)

    def set_board_status_1(self, status):
        label = [self.Indicator_1, self.Indicator_2, self.Indicator_3, self.Indicator_4]
        self.set_label(label, 0, status)
        pass

    def set_board_status_2(self, status):
        label = [self.Indicator_1, self.Indicator_2, self.Indicator_3, self.Indicator_4]
        self.set_label(label, 1, status)
        pass

    def set_board_status_3(self, status):
        label = [self.Indicator_1, self.Indicator_2, self.Indicator_3, self.Indicator_4]
        self.set_label(label, 2, status)
        pass

    def set_board_status_4(self, status):
        label = [self.Indicator_1, self.Indicator_2, self.Indicator_3, self.Indicator_4]
        self.set_label(label, 3, status)
        pass

    def InMode4in1(self):
        return bool(self.Mode4in1.checkState())

    def barcodes_1(self):
        barcodes = [str(self.sn_lineEdit_1_1.text()),
                    str(self.sn_lineEdit_1_2.text()),
                    str(self.sn_lineEdit_1_3.text()),
                    str(self.sn_lineEdit_1_4.text()),
                    str(self.sn_lineEdit_1_5.text()),
                    str(self.sn_lineEdit_1_6.text()),
                    str(self.sn_lineEdit_1_7.text()),
                    str(self.sn_lineEdit_1_8.text()),
                    str(self.sn_lineEdit_1_9.text()),
                    str(self.sn_lineEdit_1_10.text()),
                    str(self.sn_lineEdit_1_11.text()),
                    str(self.sn_lineEdit_1_12.text()),
                    str(self.sn_lineEdit_1_13.text()),
                    str(self.sn_lineEdit_1_14.text()),
                    str(self.sn_lineEdit_1_15.text()),
                    str(self.sn_lineEdit_1_16.text())]
        for i in barcodes:
            if not i:
                i = ""
        return barcodes

    def cabel_barcodes_1(self):
        cabel_barcodes = [str(self.CablelineEdit_1_1.text()),
                          str(self.CablelineEdit_1_2.text()),
                          str(self.CablelineEdit_1_3.text()),
                          str(self.CablelineEdit_1_4.text()),
                          str(self.CablelineEdit_1_5.text()),
                          str(self.CablelineEdit_1_6.text()),
                          str(self.CablelineEdit_1_7.text()),
                          str(self.CablelineEdit_1_8.text()),
                          str(self.CablelineEdit_1_9.text()),
                          str(self.CablelineEdit_1_10.text()),
                          str(self.CablelineEdit_1_11.text()),
                          str(self.CablelineEdit_1_12.text()),
                          str(self.CablelineEdit_1_13.text()),
                          str(self.CablelineEdit_1_14.text()),
                          str(self.CablelineEdit_1_15.text()),
                          str(self.CablelineEdit_1_16.text())]
        for i in cabel_barcodes:
            if not i:
                i = ""
        return cabel_barcodes

    def capacitor_barcodes_1(self):
        capacitor_barcodes = [str(self.BatterylineEdit_1_1.text()),
                          str(self.BatterylineEdit_1_2.text()),
                          str(self.BatterylineEdit_1_3.text()),
                          str(self.BatterylineEdit_1_4.text()),
                          str(self.BatterylineEdit_1_5.text()),
                          str(self.BatterylineEdit_1_6.text()),
                          str(self.BatterylineEdit_1_7.text()),
                          str(self.BatterylineEdit_1_8.text()),
                          str(self.BatterylineEdit_1_9.text()),
                          str(self.BatterylineEdit_1_10.text()),
                          str(self.BatterylineEdit_1_11.text()),
                          str(self.BatterylineEdit_1_12.text()),
                          str(self.BatterylineEdit_1_13.text()),
                          str(self.BatterylineEdit_1_14.text()),
                          str(self.BatterylineEdit_1_15.text()),
                          str(self.BatterylineEdit_1_16.text())]
        for i in capacitor_barcodes:
            if not i:
                i = ""
        return capacitor_barcodes

    def barcodes_2(self):
        barcodes = [str(self.sn_lineEdit_2_1.text()),
                    str(self.sn_lineEdit_2_2.text()),
                    str(self.sn_lineEdit_2_3.text()),
                    str(self.sn_lineEdit_2_4.text()),
                    str(self.sn_lineEdit_2_5.text()),
                    str(self.sn_lineEdit_2_6.text()),
                    str(self.sn_lineEdit_2_7.text()),
                    str(self.sn_lineEdit_2_8.text()),
                    str(self.sn_lineEdit_2_9.text()),
                    str(self.sn_lineEdit_2_10.text()),
                    str(self.sn_lineEdit_2_11.text()),
                    str(self.sn_lineEdit_2_12.text()),
                    str(self.sn_lineEdit_2_13.text()),
                    str(self.sn_lineEdit_2_14.text()),
                    str(self.sn_lineEdit_2_15.text()),
                    str(self.sn_lineEdit_2_16.text())]
        for i in barcodes:
            if not i:
                i = ""
        return barcodes

    def cabel_barcodes_2(self):
        cabel_barcodes = [str(self.CablelineEdit_2_1.text()),
                          str(self.CablelineEdit_2_2.text()),
                          str(self.CablelineEdit_2_3.text()),
                          str(self.CablelineEdit_2_4.text()),
                          str(self.CablelineEdit_2_5.text()),
                          str(self.CablelineEdit_2_6.text()),
                          str(self.CablelineEdit_2_7.text()),
                          str(self.CablelineEdit_2_8.text()),
                          str(self.CablelineEdit_2_9.text()),
                          str(self.CablelineEdit_2_10.text()),
                          str(self.CablelineEdit_2_11.text()),
                          str(self.CablelineEdit_2_12.text()),
                          str(self.CablelineEdit_2_13.text()),
                          str(self.CablelineEdit_2_14.text()),
                          str(self.CablelineEdit_2_15.text()),
                          str(self.CablelineEdit_2_16.text())]
        for i in cabel_barcodes:
            if not i:
                i = ""
        return cabel_barcodes

    def capacitor_barcodes_2(self):
        capacitor_barcodes = [str(self.BatterylineEdit_2_1.text()),
                          str(self.BatterylineEdit_2_2.text()),
                          str(self.BatterylineEdit_2_3.text()),
                          str(self.BatterylineEdit_2_4.text()),
                          str(self.BatterylineEdit_2_5.text()),
                          str(self.BatterylineEdit_2_6.text()),
                          str(self.BatterylineEdit_2_7.text()),
                          str(self.BatterylineEdit_2_8.text()),
                          str(self.BatterylineEdit_2_9.text()),
                          str(self.BatterylineEdit_2_10.text()),
                          str(self.BatterylineEdit_2_11.text()),
                          str(self.BatterylineEdit_2_12.text()),
                          str(self.BatterylineEdit_2_13.text()),
                          str(self.BatterylineEdit_2_14.text()),
                          str(self.BatterylineEdit_2_15.text()),
                          str(self.BatterylineEdit_2_16.text())]
        for i in capacitor_barcodes:
            if not i:
                i = ""
        return capacitor_barcodes

    def barcodes_3(self):
        barcodes = [str(self.sn_lineEdit_3_1.text()),
                    str(self.sn_lineEdit_3_2.text()),
                    str(self.sn_lineEdit_3_3.text()),
                    str(self.sn_lineEdit_3_4.text()),
                    str(self.sn_lineEdit_3_5.text()),
                    str(self.sn_lineEdit_3_6.text()),
                    str(self.sn_lineEdit_3_7.text()),
                    str(self.sn_lineEdit_3_8.text()),
                    str(self.sn_lineEdit_3_9.text()),
                    str(self.sn_lineEdit_3_10.text()),
                    str(self.sn_lineEdit_3_11.text()),
                    str(self.sn_lineEdit_3_12.text()),
                    str(self.sn_lineEdit_3_13.text()),
                    str(self.sn_lineEdit_3_14.text()),
                    str(self.sn_lineEdit_3_15.text()),
                    str(self.sn_lineEdit_3_16.text())]
        for i in barcodes:
            if not i:
                i = ""
        return barcodes

    def cabel_barcodes_3(self):
        cabel_barcodes = [str(self.CablelineEdit_3_1.text()),
                          str(self.CablelineEdit_3_2.text()),
                          str(self.CablelineEdit_3_3.text()),
                          str(self.CablelineEdit_3_4.text()),
                          str(self.CablelineEdit_3_5.text()),
                          str(self.CablelineEdit_3_6.text()),
                          str(self.CablelineEdit_3_7.text()),
                          str(self.CablelineEdit_3_8.text()),
                          str(self.CablelineEdit_3_9.text()),
                          str(self.CablelineEdit_3_10.text()),
                          str(self.CablelineEdit_3_11.text()),
                          str(self.CablelineEdit_3_12.text()),
                          str(self.CablelineEdit_3_13.text()),
                          str(self.CablelineEdit_3_14.text()),
                          str(self.CablelineEdit_3_15.text()),
                          str(self.CablelineEdit_3_16.text())]
        for i in cabel_barcodes:
            if not i:
                i = ""
        return cabel_barcodes

    def capacitor_barcodes_3(self):
        capacitor_barcodes = [str(self.BatterylineEdit_3_1.text()),
                          str(self.BatterylineEdit_3_2.text()),
                          str(self.BatterylineEdit_3_3.text()),
                          str(self.BatterylineEdit_3_4.text()),
                          str(self.BatterylineEdit_3_5.text()),
                          str(self.BatterylineEdit_3_6.text()),
                          str(self.BatterylineEdit_3_7.text()),
                          str(self.BatterylineEdit_3_8.text()),
                          str(self.BatterylineEdit_3_9.text()),
                          str(self.BatterylineEdit_3_10.text()),
                          str(self.BatterylineEdit_3_11.text()),
                          str(self.BatterylineEdit_3_12.text()),
                          str(self.BatterylineEdit_3_13.text()),
                          str(self.BatterylineEdit_3_14.text()),
                          str(self.BatterylineEdit_3_15.text()),
                          str(self.BatterylineEdit_3_16.text())]
        for i in capacitor_barcodes:
            if not i:
                i = ""
        return capacitor_barcodes

    def barcodes_4(self):
        barcodes = [str(self.sn_lineEdit_4_1.text()),
                    str(self.sn_lineEdit_4_2.text()),
                    str(self.sn_lineEdit_4_3.text()),
                    str(self.sn_lineEdit_4_4.text()),
                    str(self.sn_lineEdit_4_5.text()),
                    str(self.sn_lineEdit_4_6.text()),
                    str(self.sn_lineEdit_4_7.text()),
                    str(self.sn_lineEdit_4_8.text()),
                    str(self.sn_lineEdit_4_9.text()),
                    str(self.sn_lineEdit_4_10.text()),
                    str(self.sn_lineEdit_4_11.text()),
                    str(self.sn_lineEdit_4_12.text()),
                    str(self.sn_lineEdit_4_13.text()),
                    str(self.sn_lineEdit_4_14.text()),
                    str(self.sn_lineEdit_4_15.text()),
                    str(self.sn_lineEdit_4_16.text())]
        for i in barcodes:
            if not i:
                i = ""
        return barcodes

    def cabel_barcodes_4(self):
        cabel_barcodes = [str(self.CablelineEdit_4_1.text()),
                          str(self.CablelineEdit_4_2.text()),
                          str(self.CablelineEdit_4_3.text()),
                          str(self.CablelineEdit_4_4.text()),
                          str(self.CablelineEdit_4_5.text()),
                          str(self.CablelineEdit_4_6.text()),
                          str(self.CablelineEdit_4_7.text()),
                          str(self.CablelineEdit_4_8.text()),
                          str(self.CablelineEdit_4_9.text()),
                          str(self.CablelineEdit_4_10.text()),
                          str(self.CablelineEdit_4_11.text()),
                          str(self.CablelineEdit_4_12.text()),
                          str(self.CablelineEdit_4_13.text()),
                          str(self.CablelineEdit_4_14.text()),
                          str(self.CablelineEdit_4_15.text()),
                          str(self.CablelineEdit_4_16.text())]
        for i in cabel_barcodes:
            if not i:
                i = ""
        return cabel_barcodes

    def capacitor_barcodes_4(self):
        capacitor_barcodes = [str(self.BatterylineEdit_4_1.text()),
                          str(self.BatterylineEdit_4_2.text()),
                          str(self.BatterylineEdit_4_3.text()),
                          str(self.BatterylineEdit_4_4.text()),
                          str(self.BatterylineEdit_4_5.text()),
                          str(self.BatterylineEdit_4_6.text()),
                          str(self.BatterylineEdit_4_7.text()),
                          str(self.BatterylineEdit_4_8.text()),
                          str(self.BatterylineEdit_4_9.text()),
                          str(self.BatterylineEdit_4_10.text()),
                          str(self.BatterylineEdit_4_11.text()),
                          str(self.BatterylineEdit_4_12.text()),
                          str(self.BatterylineEdit_4_13.text()),
                          str(self.BatterylineEdit_4_14.text()),
                          str(self.BatterylineEdit_4_15.text()),
                          str(self.BatterylineEdit_4_16.text())]
        for i in capacitor_barcodes:
            if not i:
                i = ""
        return capacitor_barcodes

    def comboBox_update(self):
        current_pn = self.partNum_comboBox.currentText()
        self.config_model.setFilter("PARTNUMBER='" + current_pn + "'")
        self.config_model.select()
        descrip = self.config_model.record(0).value('DESCRIPTION').toString()
        self.descriptionLabel.setText(descrip)

    def update_table(self):
        filter_combo = "PARTNUMBER = '" + self.partNum_comboBox.currentText() \
                       + "' AND REVISION = '" \
                       + self.revision_comboBox.currentText() + "'"
        self.test_item_model.setFilter(filter_combo)
        self.test_item_model.select()
        self.test_item_tableView.hideColumn(0)
        self.test_item_tableView.resizeColumnsToContents()

    def testItem_update(self):
        self.comboBox_update()
        self.update_table()

    def submit_config(self):
        result = self.test_item_model.submitAll()
        msg = QtGui.QMessageBox()
        if result:
            sync_config("sqlite:///" + CONFIG_DB, CONFIG_FILE, direction="out")
            msg.setText("Update Success!")
            msg.exec_()
        else:
            error_msg = self.test_item_model.lastError().text()
            msg.critical(msg, "error", error_msg)

    def search(self):
        if self.search_lineEdit.text():
            self.search_result_label.setText("")
            barcode = str(self.search_lineEdit.text())

            self.log_model.record().indexOf("id")
            self.log_model.setFilter("barcode = '" + barcode + "'")
            self.log_model.select()

            if self.log_model.rowCount() == 0:
                self.search_result_label.setText("No Item Found")

            self.log_tableView.resizeColumnsToContents()

    def print_time(self, sec):
        min = sec // 60
        sec -= min * 60
        sec = str(sec) if sec >= 10 else "0" + str(sec)
        self.lcdNumber.display(str(min) + ":" + sec)

    def config_edit_toggle(self, toggle_bool):
        if not toggle_bool:
            self.test_item_tableView.setEditTriggers(
                QtGui.QAbstractItemView.NoEditTriggers)
        else:
            dialog = LoginDialog()
            if dialog.exec_():
                self.checkBox.setChecked(True)
                self.test_item_tableView.setEditTriggers(
                    QtGui.QAbstractItemView.DoubleClicked)
            else:
                self.checkBox.setChecked(False)

    def switch_between_mode4in1(self, toggle):
        if toggle:
            self.groupBox1_2.setDisabled(True)
            self.groupBox1_3.setDisabled(True)
            self.groupBox1_4.setDisabled(True)
            self.groupBox1_6.setDisabled(True)
            self.groupBox1_7.setDisabled(True)
            self.groupBox1_8.setDisabled(True)
            self.groupBox1_10.setDisabled(True)
            self.groupBox1_11.setDisabled(True)
            self.groupBox1_12.setDisabled(True)
            self.groupBox1_14.setDisabled(True)
            self.groupBox1_15.setDisabled(True)
            self.groupBox1_16.setDisabled(True)
            self.groupBox2_2.setDisabled(True)
            self.groupBox2_3.setDisabled(True)
            self.groupBox2_4.setDisabled(True)
            self.groupBox2_6.setDisabled(True)
            self.groupBox2_7.setDisabled(True)
            self.groupBox2_8.setDisabled(True)
            self.groupBox2_10.setDisabled(True)
            self.groupBox2_11.setDisabled(True)
            self.groupBox2_12.setDisabled(True)
            self.groupBox2_14.setDisabled(True)
            self.groupBox2_15.setDisabled(True)
            self.groupBox2_16.setDisabled(True)
            self.groupBox3_2.setDisabled(True)
            self.groupBox3_3.setDisabled(True)
            self.groupBox3_4.setDisabled(True)
            self.groupBox3_6.setDisabled(True)
            self.groupBox3_7.setDisabled(True)
            self.groupBox3_8.setDisabled(True)
            self.groupBox3_10.setDisabled(True)
            self.groupBox3_11.setDisabled(True)
            self.groupBox3_12.setDisabled(True)
            self.groupBox3_14.setDisabled(True)
            self.groupBox3_15.setDisabled(True)
            self.groupBox3_16.setDisabled(True)
            self.groupBox4_2.setDisabled(True)
            self.groupBox4_3.setDisabled(True)
            self.groupBox4_4.setDisabled(True)
            self.groupBox4_6.setDisabled(True)
            self.groupBox4_7.setDisabled(True)
            self.groupBox4_8.setDisabled(True)
            self.groupBox4_10.setDisabled(True)
            self.groupBox4_11.setDisabled(True)
            self.groupBox4_12.setDisabled(True)
            self.groupBox4_14.setDisabled(True)
            self.groupBox4_15.setDisabled(True)
            self.groupBox4_16.setDisabled(True)
            self.sn_lineEdit_1_2.clear()
            self.sn_lineEdit_1_3.clear()
            self.sn_lineEdit_1_4.clear()
            self.sn_lineEdit_1_6.clear()
            self.sn_lineEdit_1_7.clear()
            self.sn_lineEdit_1_8.clear()
            self.sn_lineEdit_1_10.clear()
            self.sn_lineEdit_1_11.clear()
            self.sn_lineEdit_1_12.clear()
            self.sn_lineEdit_1_14.clear()
            self.sn_lineEdit_1_15.clear()
            self.sn_lineEdit_1_16.clear()
            self.sn_lineEdit_2_2.clear()
            self.sn_lineEdit_2_3.clear()
            self.sn_lineEdit_2_4.clear()
            self.sn_lineEdit_2_6.clear()
            self.sn_lineEdit_2_7.clear()
            self.sn_lineEdit_2_8.clear()
            self.sn_lineEdit_2_10.clear()
            self.sn_lineEdit_2_11.clear()
            self.sn_lineEdit_2_12.clear()
            self.sn_lineEdit_2_14.clear()
            self.sn_lineEdit_2_15.clear()
            self.sn_lineEdit_2_16.clear()
            self.sn_lineEdit_3_2.clear()
            self.sn_lineEdit_3_3.clear()
            self.sn_lineEdit_3_4.clear()
            self.sn_lineEdit_3_6.clear()
            self.sn_lineEdit_3_7.clear()
            self.sn_lineEdit_3_8.clear()
            self.sn_lineEdit_3_10.clear()
            self.sn_lineEdit_3_11.clear()
            self.sn_lineEdit_3_12.clear()
            self.sn_lineEdit_3_14.clear()
            self.sn_lineEdit_3_15.clear()
            self.sn_lineEdit_3_16.clear()
            self.sn_lineEdit_4_2.clear()
            self.sn_lineEdit_4_3.clear()
            self.sn_lineEdit_4_4.clear()
            self.sn_lineEdit_4_6.clear()
            self.sn_lineEdit_4_7.clear()
            self.sn_lineEdit_4_8.clear()
            self.sn_lineEdit_4_10.clear()
            self.sn_lineEdit_4_11.clear()
            self.sn_lineEdit_4_12.clear()
            self.sn_lineEdit_4_14.clear()
            self.sn_lineEdit_4_15.clear()
            self.sn_lineEdit_4_16.clear()
            self.CablelineEdit_1_2.clear()
            self.CablelineEdit_1_3.clear()
            self.CablelineEdit_1_4.clear()
            self.CablelineEdit_1_6.clear()
            self.CablelineEdit_1_7.clear()
            self.CablelineEdit_1_8.clear()
            self.CablelineEdit_1_10.clear()
            self.CablelineEdit_1_11.clear()
            self.CablelineEdit_1_12.clear()
            self.CablelineEdit_1_14.clear()
            self.CablelineEdit_1_15.clear()
            self.CablelineEdit_1_16.clear()
            self.CablelineEdit_2_2.clear()
            self.CablelineEdit_2_3.clear()
            self.CablelineEdit_2_4.clear()
            self.CablelineEdit_2_6.clear()
            self.CablelineEdit_2_7.clear()
            self.CablelineEdit_2_8.clear()
            self.CablelineEdit_2_10.clear()
            self.CablelineEdit_2_11.clear()
            self.CablelineEdit_2_12.clear()
            self.CablelineEdit_2_14.clear()
            self.CablelineEdit_2_15.clear()
            self.CablelineEdit_2_16.clear()
            self.CablelineEdit_3_2.clear()
            self.CablelineEdit_3_3.clear()
            self.CablelineEdit_3_4.clear()
            self.CablelineEdit_3_6.clear()
            self.CablelineEdit_3_7.clear()
            self.CablelineEdit_3_8.clear()
            self.CablelineEdit_3_10.clear()
            self.CablelineEdit_3_11.clear()
            self.CablelineEdit_3_12.clear()
            self.CablelineEdit_3_14.clear()
            self.CablelineEdit_3_15.clear()
            self.CablelineEdit_3_16.clear()
            self.CablelineEdit_4_2.clear()
            self.CablelineEdit_4_3.clear()
            self.CablelineEdit_4_4.clear()
            self.CablelineEdit_4_6.clear()
            self.CablelineEdit_4_7.clear()
            self.CablelineEdit_4_8.clear()
            self.CablelineEdit_4_10.clear()
            self.CablelineEdit_4_11.clear()
            self.CablelineEdit_4_12.clear()
            self.CablelineEdit_4_14.clear()
            self.CablelineEdit_4_15.clear()
            self.CablelineEdit_4_16.clear()
            self.BatterylineEdit_1_2.clear()
            self.BatterylineEdit_1_3.clear()
            self.BatterylineEdit_1_4.clear()
            self.BatterylineEdit_1_6.clear()
            self.BatterylineEdit_1_7.clear()
            self.BatterylineEdit_1_8.clear()
            self.BatterylineEdit_1_10.clear()
            self.BatterylineEdit_1_11.clear()
            self.BatterylineEdit_1_12.clear()
            self.BatterylineEdit_1_14.clear()
            self.BatterylineEdit_1_15.clear()
            self.BatterylineEdit_1_16.clear()
            self.BatterylineEdit_2_2.clear()
            self.BatterylineEdit_2_3.clear()
            self.BatterylineEdit_2_4.clear()
            self.BatterylineEdit_2_6.clear()
            self.BatterylineEdit_2_7.clear()
            self.BatterylineEdit_2_8.clear()
            self.BatterylineEdit_2_10.clear()
            self.BatterylineEdit_2_11.clear()
            self.BatterylineEdit_2_12.clear()
            self.BatterylineEdit_2_14.clear()
            self.BatterylineEdit_2_15.clear()
            self.BatterylineEdit_2_16.clear()
            self.BatterylineEdit_3_2.clear()
            self.BatterylineEdit_3_3.clear()
            self.BatterylineEdit_3_4.clear()
            self.BatterylineEdit_3_6.clear()
            self.BatterylineEdit_3_7.clear()
            self.BatterylineEdit_3_8.clear()
            self.BatterylineEdit_3_10.clear()
            self.BatterylineEdit_3_11.clear()
            self.BatterylineEdit_3_12.clear()
            self.BatterylineEdit_3_14.clear()
            self.BatterylineEdit_3_15.clear()
            self.BatterylineEdit_3_16.clear()
            self.BatterylineEdit_4_2.clear()
            self.BatterylineEdit_4_3.clear()
            self.BatterylineEdit_4_4.clear()
            self.BatterylineEdit_4_6.clear()
            self.BatterylineEdit_4_7.clear()
            self.BatterylineEdit_4_8.clear()
            self.BatterylineEdit_4_10.clear()
            self.BatterylineEdit_4_11.clear()
            self.BatterylineEdit_4_12.clear()
            self.BatterylineEdit_4_14.clear()
            self.BatterylineEdit_4_15.clear()
            self.BatterylineEdit_4_16.clear()

        else:
            self.groupBox1_2.setEnabled(True)
            self.groupBox1_3.setEnabled(True)
            self.groupBox1_4.setEnabled(True)
            self.groupBox1_6.setEnabled(True)
            self.groupBox1_7.setEnabled(True)
            self.groupBox1_8.setEnabled(True)
            self.groupBox1_10.setEnabled(True)
            self.groupBox1_11.setEnabled(True)
            self.groupBox1_12.setEnabled(True)
            self.groupBox1_14.setEnabled(True)
            self.groupBox1_15.setEnabled(True)
            self.groupBox1_16.setEnabled(True)
            self.groupBox2_2.setEnabled(True)
            self.groupBox2_3.setEnabled(True)
            self.groupBox2_4.setEnabled(True)
            self.groupBox2_6.setEnabled(True)
            self.groupBox2_7.setEnabled(True)
            self.groupBox2_8.setEnabled(True)
            self.groupBox2_10.setEnabled(True)
            self.groupBox2_11.setEnabled(True)
            self.groupBox2_12.setEnabled(True)
            self.groupBox2_14.setEnabled(True)
            self.groupBox2_15.setEnabled(True)
            self.groupBox2_16.setEnabled(True)
            self.groupBox3_2.setEnabled(True)
            self.groupBox3_3.setEnabled(True)
            self.groupBox3_4.setEnabled(True)
            self.groupBox3_6.setEnabled(True)
            self.groupBox3_7.setEnabled(True)
            self.groupBox3_8.setEnabled(True)
            self.groupBox3_10.setEnabled(True)
            self.groupBox3_11.setEnabled(True)
            self.groupBox3_12.setEnabled(True)
            self.groupBox3_14.setEnabled(True)
            self.groupBox3_15.setEnabled(True)
            self.groupBox3_16.setEnabled(True)
            self.groupBox4_2.setEnabled(True)
            self.groupBox4_3.setEnabled(True)
            self.groupBox4_4.setEnabled(True)
            self.groupBox4_6.setEnabled(True)
            self.groupBox4_7.setEnabled(True)
            self.groupBox4_8.setEnabled(True)
            self.groupBox4_10.setEnabled(True)
            self.groupBox4_11.setEnabled(True)
            self.groupBox4_12.setEnabled(True)
            self.groupBox4_14.setEnabled(True)
            self.groupBox4_15.setEnabled(True)
            self.groupBox4_16.setEnabled(True)

                # def login(self):
                # dialog = LoginDialog()
                # if dialog.exec_():
                #         self.checkBox.setChecked(True)
                #     else:
                #         self.checkBox.setChecked(False)


if __name__ == "__main__":
    a = QtGui.QApplication(sys.argv)
    Form = QtGui.QWidget()
    w = UFT_UiHandler()
    w.setupUi(Form)
    w.setupWidget(Form)
    Form.show()
    sys.exit(a.exec_())
