# -*- coding: utf-8 -*-
import sys
import os
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui
from RegXMLParser import RegXMLParser
from OutputRegWindow import OutputReg

Version = "V2.1"

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self)

        self.resize(600, 600)
        self.setWindowTitle('ISPRegisterTool '+Version)

        self.output_reg = OutputReg()

        self.file_menu_open = QtWidgets.QAction('Open header file', self)
        self.file_menu_open.triggered.connect(self.FileDialog)

        self.file_menu_initfile = QtWidgets.QAction('Open initial value file', self)
        # self.file_menu_initfile.connect(self.file_menu_initfile, QtCore.SIGNAL('triggered()'), self.InitValueFile)
        self.file_menu_initfile.setDisabled(1)

        self.file_menu_outreg = QtWidgets.QAction('Output Register doc file', self)
        self.file_menu_outreg.triggered.connect(self.OutputRegDoc)
        self.file_menu_outreg.setDisabled(1)


        menubar = self.menuBar()
        file = menubar.addMenu('File')
        file.addAction(self.file_menu_open)
        file.addAction(self.file_menu_initfile)
        file.addAction(self.file_menu_outreg)

        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)

        hbox_layout = QtWidgets.QHBoxLayout()

        vbox_layout = QtWidgets.QVBoxLayout()
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.itemSelectionChanged.connect(self.SetTable)
        self.text_edit = QtWidgets.QTextEdit()
        vbox_layout.addWidget(self.list_widget)
        vbox_layout.addWidget(self.text_edit)
        list_widget_policy = self.list_widget.sizePolicy()
        list_widget_policy.setVerticalStretch(1)
        text_edit_policy = self.text_edit.sizePolicy()
        text_edit_policy.setVerticalStretch(2)
        self.list_widget.setSizePolicy(list_widget_policy)
        self.text_edit.setSizePolicy(text_edit_policy)


        self.table_widget = QtWidgets.QTableWidget(1, 3)
        self.table_widget.setHorizontalHeaderLabels(['ParaName', 'Cal Size', 'Real Offset'])

        hbox_layout.addLayout(vbox_layout, 1)
        hbox_layout.addWidget(self.table_widget, 3)

        main_widget.setLayout(hbox_layout)
    
    def FileDialog(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', './')
        print(filename[0])
        if filename[0]:
            current_dir = os.getcwd()
            cmd = current_dir + '/castxml/bin/castxml.exe %s --castxml-gccxml -o result.xml'%(filename[0])
            info = os.system(cmd)
            if info == 1:
                QtWidgets.QMessageBox.critical(self, "Critical", 'ERROR!! Please check file')
                return
            self.parser = RegXMLParser(current_dir+'/result.xml')
            self.list_widget.itemSelectionChanged.disconnect(self.SetTable)
            self.list_widget.clear()
            self.list_widget.itemSelectionChanged.connect(self.SetTable)
            self.table_widget.clear()
            self.table_widget.setHorizontalHeaderLabels(['ParaName', 'Cal Size', 'Real Offset'])
            self.file_menu_initfile.setDisabled(1)
            self.file_menu_outreg.setDisabled(1)

            for struct in self.parser.get_struct_element():
                if struct.attrib['name'] != '__NSConstantString_tag':
                    struct_name = self.parser.get_struct_name_by_id(struct.attrib['id'])
                    list_widget_item = QtWidgets.QListWidgetItem(struct_name)
                    self.list_widget.addItem(list_widget_item)

            self.file_menu_outreg.setEnabled(1)
    
    def _ListToString(self, lst):
        length = len(lst)
        if length > 0:
            lst_string = ''
            for l in lst:
                lst_string += '[%d]'%(l)
            return lst_string
        else:
            return ''
    
    def SetTable(self):
        currentItem = self.list_widget.currentItem()
        #Typedef(name)-->Typedef(type)-->Struct(id)-->members-->element_member_list
        member_elem_lst = self.parser.get_struct_member(self.parser.get_element_by_id(self.parser.get_element_by_name(currentItem.text()).attrib['type']))
        self.table_widget.setRowCount(len(member_elem_lst));
        row = 0
        error_flag = 0
        member_lst = self.parser.analyze_member_element_list(member_elem_lst)
        for i,memb in enumerate(member_lst):
            Item = QtWidgets.QTableWidgetItem(memb['name']+self._ListToString(memb['array_list']))
            self.table_widget.setItem(row, 0, Item)

            if i > 0:
                cal_offset = member_lst[i-1]['cal_size']+int(member_lst[i-1]['offset'])
            else:
                cal_offset = 0
            Item = QtWidgets.QTableWidgetItem(str('%d'%cal_offset))
            self.table_widget.setItem(row, 1, Item)

            Item = QtWidgets.QTableWidgetItem(memb['offset'])
            self.table_widget.setItem(row, 2, Item)

            if cal_offset != int(memb['offset']):
                error_flag = 1
                for i in range(3):
                    self.table_widget.item(row, i).setBackground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
                    # print(type(self.table_widget.item(row, i)))

            row = row + 1
        
        #如果出错误，弹框
        if error_flag == 1:
            QtWidgets.QMessageBox.critical(self, "Critical",  "offset do not satisfiy the alignment")

    def OutputRegDoc(self):
        self.output_reg.InitData(self.parser)
        self.output_reg.show()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    qb = MainWindow()
    qb.show()
    sys.exit(app.exec_())