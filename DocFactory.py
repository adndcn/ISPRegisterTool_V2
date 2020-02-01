import sys
import os
import xlwt
from docx import Document

class Docx:
    def __init__(self, filename):
        self.filename = filename
    
    def open(self):
        # self.document = Document(docx=os.path.join(os.getcwd(), 'default.docx'))
        self.document = Document()

    def add_header(self, string):
        self.document.add_heading(string, level=1)
        self.table = self.document.add_table(rows=1, cols=4)
        self.table.style = 'Table Grid'
        hdr_cells = self.table.rows[0].cells
        hdr_cells[0].text = 'address'
        hdr_cells[1].text = 'parameter'
        hdr_cells[2].text = 'init value'
        hdr_cells[3].text = 'description'

    def write(self, address, name, init_value, description):
        row_cells = self.table.add_row().cells
        row_cells[0].text = str('0x%x'%(address))
        row_cells[1].text = name
        row_cells[2].text = str('0x%02x'%(init_value))
        row_cells[3].text = description
    
    def close(self):
        self.document.save(self.filename)

class Excel:
    def __init__(self, filename):
        self.filename = filename
    
    def write(self):
        print("Excel")

class Txt:
    def __init__(self, filename):
        self.filename = filename
    
    def open(self):
        self.file = open(self.filename, 'w')
    
    def add_header(self, string):
        self.file.write('TITLE: ' + string + '\n')
    
    def write(self, address, name, init_value, description):
        self.file.write('0x%x '%address)
        self.file.write(name+' ')
        self.file.write('0x%02x '%init_value)
        self.file.write(description)
        self.file.write('\n')
    
    def close(self):
        self.file.close()

class Sysout:
    def open(self):
        pass
    
    def add_header(self, string):
        print('TITLE: ' + string)
    
    def write(self, address, name, init_value, description):
        print('0x%x %s %02x %s'%(address, name, init_value, description))
    
    def close(self):
        pass

class DocFactory:
    @staticmethod
    def doc_generator(filename):
        if ".docx" in filename:
            return Docx(filename)
        elif "xls" in filename:
            return Excel(filename)
        elif ".txt" in filename:
            return Txt(filename)
        else:
            return Sysout()

if __name__ == "__main__":
    file = DocFactory.doc_generator("hh")
    file.open()
    file.add_header("hh")
    file.write(0x8000, 'test', 0x2, 'des')
    file.write(0x8000, 'test', 0x2, 'des')
    file.add_header("hh")
    file.write(0x8000, 'test', 0x2, 'des')
    file.write(0x8000, 'test', 0x2, 'des')
    file.close()

        


