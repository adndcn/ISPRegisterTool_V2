# -*- coding: utf-8 -*-
import sys
import os
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui
import re
from RegXMLParser import RegXMLParser
from DocFactory import DocFactory

class FileWriteThread(QtCore.QThread):

    countChanged = QtCore.pyqtSignal(int)
    def __init__(self, filename, name_list, addr_list, expand_title_list, parser):
        super().__init__()
        self.filename = filename
        self.name_list = name_list
        self.addr_list = addr_list
        self.parser = parser
        self.expand_title_list = expand_title_list
        

    def run(self):
        self.countChanged.emit(10)
        file = DocFactory.doc_generator(self.filename)
        self.countChanged.emit(15)
        length = len(self.name_list)
        file.open()
        for i,name in enumerate(self.name_list):
            base_addr = self.addr_list[i]
            self.parser.file_write(self.parser.get_element_by_id(self.parser.get_element_by_name(name).attrib['type']), base_addr, file, self.expand_title_list[i])
            self.countChanged.emit((i+1)*80/length+15)
        file.close()
        self.countChanged.emit(100)


class OutputReg(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.setWindowTitle('Output Register document')

        grid_layout = QtWidgets.QGridLayout()
        para_label = QtWidgets.QLabel('Parameters')
        self.out_list_widget = QtWidgets.QListWidget()
        grid_layout.addWidget(para_label, 0, 0, 1, 2)
        grid_layout.addWidget(self.out_list_widget, 1, 0, 1, 2)

        base_addr_label = QtWidgets.QLabel('base addr')
        hex_label = QtWidgets.QLabel('0x')
        self.out_addr_edit = QtWidgets.QLineEdit()
        self.expand_title = QtWidgets.QCheckBox('Expand Title')
        self.expand_title.setCheckState(QtCore.Qt.Checked)
        horizontal_layout = QtWidgets.QHBoxLayout()
        horizontal_layout.addWidget(hex_label)
        horizontal_layout.addWidget(self.out_addr_edit)
        horizontal_layout.addWidget(self.expand_title)
        grid_layout.addWidget(base_addr_label, 2, 0, 1, 2)
        grid_layout.addLayout(horizontal_layout, 3, 0)
        # grid_layout.addWidget(hex_label, 3, 0)
        # grid_layout.addWidget(self.out_addr_edit, 3, 1)

        self.little_endian = QtWidgets.QCheckBox('Little Endian')
        self.byte_expand = QtWidgets.QCheckBox('Byte Expand')
        self.byte_expand.setCheckState(QtCore.Qt.Checked)
        self.remove_reserved = QtWidgets.QCheckBox('Remove Reserved')
        self.remove_reserved.setCheckState(QtCore.Qt.Checked)
        vertial_layout = QtWidgets.QVBoxLayout()
        vertial_layout.addWidget(self.little_endian)
        vertial_layout.addWidget(self.byte_expand)
        vertial_layout.addWidget(self.remove_reserved)
        grid_layout.addLayout(vertial_layout, 1, 2)

        self.add_button = QtWidgets.QPushButton("Add-->")
        self.add_button.clicked.connect(self.AddItem)
        grid_layout.addWidget(self.add_button, 2, 2)

        self.out_table_widget = QtWidgets.QTableWidget(1,2)
        self.out_table_widget.setHorizontalHeaderLabels(['ParaName', 'base addr'])
        self.out_delete_button = QtWidgets.QPushButton("Delete Item")
        self.out_delete_button.clicked.connect(self.DeleteItem)
        grid_layout.addWidget(self.out_table_widget, 0, 3, 3, 2)
        grid_layout.addWidget(self.out_delete_button, 3, 3)

        self.out_generate_button = QtWidgets.QPushButton("Generate")
        self.out_generate_button.clicked.connect(self.Generate)
        grid_layout.addWidget(self.out_generate_button, 3, 4)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setValue(0)
        grid_layout.addWidget(self.progress_bar, 4, 0, 1, 5)

        self.setLayout(grid_layout)

        self.row = 0
        
        self.expand_title_list = []
    
    def InitData(self, parser):
        self.parser = parser
        self.out_list_widget.clear()
        self.out_table_widget.clearContents()
        self.row = 0
        for struct in self.parser.get_struct_element():
            if struct.attrib['name'] != '__NSConstantString_tag':
                struct_name = self.parser.get_struct_name_by_id(struct.attrib['id'])
                list_widget_item = QtWidgets.QListWidgetItem(struct_name)
                self.out_list_widget.addItem(list_widget_item)
        self.out_list_widget.setCurrentRow(0)
        self.progress_bar.setValue(0)
        self.expand_title_list = []
    
    def AddItem(self):
        line_text = self.out_addr_edit.text()
        patten = '[\da-fA-F]+$'
        if re.match(patten, line_text):
            self.out_table_widget.setRowCount(self.row+1)
            currentItem = self.out_list_widget.currentItem()
            base_addr = '0x'+line_text
            Item = QtWidgets.QTableWidgetItem(currentItem.text())
            self.out_table_widget.setItem(self.row, 0, Item)

            Item = QtWidgets.QTableWidgetItem(base_addr)
            self.out_table_widget.setItem(self.row, 1, Item)

            if self.expand_title.checkState() == QtCore.Qt.Checked:
                flag = True
                self.out_table_widget.item(self.row, 0).setBackground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
            else:
                flag = False
            self.expand_title_list.append(flag)

            self.row = self.row + 1
            
            

    def DeleteItem(self):
        index = self.out_table_widget.currentRow()
        if index >= 0:
            self.out_table_widget.removeRow(index)
            del self.expand_title_list[index]
            self.row = self.row - 1
            print(self.expand_title_list)
    
    def onCountChanged(self, value):
        self.progress_bar.setValue(value)
        if(value == 100):
            QtWidgets.QMessageBox.information(self, "information", "Output Register doc done.")

    def Generate(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save docx file', "untitled", "docx (*.docx);; excel (*.xls);; csv (*.csv)")
        if filename[0]:
            name_list = []
            addr_list = []
            row_count = self.out_table_widget.rowCount()
            for row in range(row_count):
                name_list.append(self.out_table_widget.item(row, 0).text())
                addr_list.append(int(self.out_table_widget.item(row, 1).text(), 16))
            self.thread = FileWriteThread(filename[0], name_list, addr_list, self.expand_title_list, self.parser)
            self.thread.countChanged.connect(self.onCountChanged)
            self.thread.start()


            


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    qb = OutputReg()
    qb.show()
    sys.exit(app.exec_())