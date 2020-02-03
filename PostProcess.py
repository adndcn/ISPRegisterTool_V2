# -*- coding: utf-8 -*-

import os
import sys
import re

class PostProcess:
    def __init__(self):
        self.files_name = []
        self.files_handle = []
        self.files_content = []
        self.reg_comment_pattern = [
                                    "\/{2,}\s*a\s*\=\s*([ua-fA-FxX\d]+)[\s\,]+v\s*\=\s*\[\s*([ua-fA-FxX\d\,\.\s]+)\s*\][\s\,]+d\s*\=\s*\"(.*)\"\s*$",#//a=0x250, v=[0x100], d="xxx"
                                    "\/{2,}\s*a\s*\=\s*([ua-fA-FxX\d]+)[\s\,]+v\s*\=\s*\[\s*(p\w+)\s*\][\s\,]+d\s*\=\s*\"(.*)\"\s*$",#//a=0x250, v=[pAECvalue], d="xxx"
                                    "\/{2,}\s*a\s*\=\s*([ua-fA-FxX\d]+)[\s\,]+v\s*\=\s*([ua-fA-FxX\d]+)[\s\,]+d\s*\=\s*\"(.*)\"\s*$",#//a=0x250, v=0x100, d="xxx"
                                    "\/{2,}\s*a\s*\=\s*([ua-fA-FxX\d]+)[\s\,]+p\s*\=\s*(\w+)[\s\,]+d\s*\=\s*\"(.*)\"",#//a=0x250, p=pW, d="xxx"

                                    "\/{2,}\s*([ua-fA-FxX\d]+)[\s\,]+v\s*\=\s*\[\s*([ua-fA-FxX\d\,\.\s]+)\s*\][\s\,]+d\s*\=\s*\"(.*)\"\s*$",#//0x250, v=[0x100], d="xxx"
                                    "\/{2,}\s*([ua-fA-FxX\d]+)[\s\,]+p\s*\=\s*(\w+)[\s\,]+d\s*\=\s*\"(.*)\"\s*$",#//0x250, p=pW, d="xxx"
                                    "\/{2,}\s*([ua-fA-FxX\d]+)[\s\,]+v\s*\=\s*\[\s*(p\w+)\s*\][\s\,]+d\s*\=\s*\"(.*)\"\s*$",#//0x250, v=[pAECvalue], d="xxx"
                                    "\/{2,}\s*([ua-fA-FxX\d]+)[\s\,]+v\s*\=\s*([ua-fA-FxX\d]+)[\s\,]+d\s*\=\s*\"(.*)\"\s*$",#//0x250, v=0x100, d="xxx"

                                    "\/{2,}\s*a\s*\=\s*([ua-fA-FxX\d]+)[\s\,]+v\s*\=\s*\[\s*([ua-fA-FxX\d\,\.\s]+)\s*\]\s*$",#//a=0x250, v=[0x100]
                                    "\/{2,}\s*a\s*\=\s*([ua-fA-FxX\d]+)[\s\,]+p\s*\=\s*(\w+)\s*$",#//a=0x250, p=pW
                                    "\/{2,}\s*a\s*\=\s*([ua-fA-FxX\d]+)[\s\,]+v\s*\=\s*\[\s*(p\w+)\s*\]\s*$",#//a=0x250, v=[pAECvalue]
                                    "\/{2,}\s*a\s*\=\s*([ua-fA-FxX\d]+)[\s\,]+v\s*\=\s*([ua-fA-FxX\d]+)\s*$",#//a=0x250, v=0x100

                                    "\/{2,}\s*([ua-fA-FxX\d]+)[\s\,]+v\s*\=\s*\[\s*([ua-fA-FxX\d\,\.\s]+)\s*\]\s*$",#//0x250, v=[0x100]
                                    "\/{2,}\s*([ua-fA-FxX\d]+)[\s\,]+p\s*\=\s*(\w+)\s*$",#//0x250, p=pW
                                    "\/{2,}\s*([ua-fA-FxX\d]+)[\s\,]+v\s*\=\s*\[\s*(p\w+)\s*\]\s*$",#//0x250, v=[pAECvalue]
                                    "\/{2,}\s*([ua-fA-FxX\d]+)[\s\,]+v\s*\=\s*([ua-fA-FxX\d]+)\s*$",#//0x250, v=0x100

                                    "\/{2,}\s*a\s*\=\s*([ua-fA-FxX\d]+)\s*$",#//a=0x250
                                    "\/{2,}\s*([ua-fA-FxX\d]+)\s*$"#//0x250
                                    ]
    
    def get_reg_comment(self, file_name, line):
        if file_name not in self.files_name:
            self.files_name.append(file_name)
            file = open(file_name, 'r')
            self.files_handle.append(file)
            file_content = file.readlines()
            self.files_content.append(file_content)
        else:
            index = self.files_name.index(file_name)
            file_content = self.files_content[index]
        
        string = file_content[int(line)-1].strip()
        member = {}
        if "//" in string:
            #有寄存器说明注释
            index = string.find("//")
            if re.match(self.reg_comment_pattern[0], string[index:]):
                #//a=0x250, v=[0x100], d="xxx"
                match = re.match(self.reg_comment_pattern[0], string[index:])
                # print(match.group(2))
                member['addr_offset'] = match.group(1)
                member['init_value'] = match.group(2)
                member['init_value_type'] = "array"
                member['description'] = match.group(3)
            elif re.match(self.reg_comment_pattern[1], string[index:]):
                #//a=0x250, v=[pAECvalue], d="xxx"
                match = re.match(self.reg_comment_pattern[1], string[index:])
                # print(match.group(2))
                member['addr_offset'] = match.group(1)
                member['init_value'] = match.group(2)
                member['init_value_type'] = "pointer"
                member['description'] = match.group(3)
            elif re.match(self.reg_comment_pattern[2], string[index:]):
                #//a=0x250, v=0x100, d="xxx"
                match = re.match(self.reg_comment_pattern[2], string[index:])
                # print(match.group(2))
                member['addr_offset'] = match.group(1)
                temp_s = match.group(2)
                if 'u' in match.group(2):
                    temp_s = match.group(2)[:match.group(2).find('u')]
                member['init_value'] = temp_s
                member['init_value_type'] = "number"
                member['description'] = match.group(3)
            elif re.match(self.reg_comment_pattern[3], string[index:]):
                #//a=0x250, p=pW, d="xxx"
                match = re.match(self.reg_comment_pattern[3], string[index:])
                # print (match.group(2))
                member['addr_offset'] = match.group(1)
                member['init_value'] = match.group(2)
                member['init_value_type'] = "pointer"
                member['description'] = match.group(3)
            elif re.match(self.reg_comment_pattern[4], string[index:]):
                #//0x250, v=[0x100], d="xxx"
                match = re.match(self.reg_comment_pattern[4], string[index:])
                # print (match.group(2))
                member['addr_offset'] = match.group(1)
                member['init_value'] = match.group(2)
                member['init_value_type'] = "array"
                member['description'] = match.group(3)
            elif re.match(self.reg_comment_pattern[5], string[index:]):
                #//0x250, p=pW, d="xxx"
                match = re.match(self.reg_comment_pattern[5], string[index:])
                # print( match.group(2))
                member['addr_offset'] = match.group(1)
                member['init_value'] = match.group(2)
                member['init_value_type'] = "pointer"
                member['description'] = match.group(3)
            elif re.match(self.reg_comment_pattern[6], string[index:]):
                #//0x250, v=[pAECvalue], d="xxx"
                match = re.match(self.reg_comment_pattern[6], string[index:])
                # print( match.group(2))
                member['addr_offset'] = match.group(1)
                member['init_value'] = match.group(2)
                member['init_value_type'] = "pointer"
                member['description'] = match.group(3)
            elif re.match(self.reg_comment_pattern[7], string[index:]):
                #//0x250, v=0x100, d="xxx"
                match = re.match(self.reg_comment_pattern[7], string[index:])
                # print( match.group(2))
                member['addr_offset'] = match.group(1)
                temp_s = match.group(2)
                if 'u' in match.group(2):
                    temp_s = match.group(2)[:match.group(2).find('u')]
                member['init_value'] = temp_s
                member['init_value_type'] = "number"
                member['description'] = match.group(3)
            elif re.match(self.reg_comment_pattern[8], string[index:]):
                #//a=0x250, v=[0x100]
                match = re.match(self.reg_comment_pattern[8], string[index:])
                # print( match.group(2))
                member['addr_offset'] = match.group(1)
                member['init_value'] = match.group(2)
                member['init_value_type'] = "array"
                member['description'] = ""
            elif re.match(self.reg_comment_pattern[9], string[index:]):
                #//a=0x250, p=pW
                match = re.match(self.reg_comment_pattern[9], string[index:])
                # print( match.group(2))
                member['addr_offset'] = match.group(1)
                member['init_value'] = match.group(2)
                member['init_value_type'] = "array"
                member['description'] = ""
            elif re.match(self.reg_comment_pattern[10], string[index:]):
                #//a=0x250, v=[pAECvalue]
                match = re.match(self.reg_comment_pattern[10], string[index:])
                # print( match.group(2))
                member['addr_offset'] = match.group(1)
                member['init_value'] = match.group(2)
                member['init_value_type'] = "array"
                member['description'] = ""
            elif re.match(self.reg_comment_pattern[11], string[index:]):
                #//a=0x250, v=0x100
                match = re.match(self.reg_comment_pattern[11], string[index:])
                # print( match.group(2))
                member['addr_offset'] = match.group(1)
                temp_s = match.group(2)
                if 'u' in match.group(2):
                    temp_s = match.group(2)[:match.group(2).find('u')]
                member['init_value'] = temp_s
                member['init_value_type'] = "number"
                member['description'] = ""
            elif re.match(self.reg_comment_pattern[12], string[index:]):
                #//0x250, v=[0x100]
                match = re.match(self.reg_comment_pattern[12], string[index:])
                # print( match.group(2))
                member['addr_offset'] = match.group(1)
                member['init_value'] = match.group(2)
                member['init_value_type'] = "array"
                member['description'] = ""
            elif re.match(self.reg_comment_pattern[13], string[index:]):
                #//0x250, p=pW
                match = re.match(self.reg_comment_pattern[13], string[index:])
                # print( match.group(2))
                member['addr_offset'] = match.group(1)
                member['init_value'] = match.group(2)
                member['init_value_type'] = "array"
                member['description'] = ""
            elif re.match(self.reg_comment_pattern[14], string[index:]):
                #//0x250, v=[pAECvalue]
                match = re.match(self.reg_comment_pattern[14], string[index:])
                # print( match.group(2))
                member['addr_offset'] = match.group(1)
                member['init_value'] = match.group(2)
                member['init_value_type'] = "array"
                member['description'] = ""
            elif re.match(self.reg_comment_pattern[15], string[index:]):
                #//0x250, v=0x100
                match = re.match(self.reg_comment_pattern[15], string[index:])
                # print( match.group(2))
                member['addr_offset'] = match.group(1)
                temp_s = match.group(2)
                if 'u' in match.group(2):
                    temp_s = match.group(2)[:match.group(2).find('u')]
                member['init_value'] = temp_s
                member['init_value_type'] = "number"
                member['description'] = ""
            elif re.match(self.reg_comment_pattern[16], string[index:]):
                #//a=0x250
                match = re.match(self.reg_comment_pattern[16], string[index:])
                # print( match.group(1))
                member['addr_offset'] = match.group(1)
                member['init_value'] = ""
                member['init_value_type'] = ""
                member['description'] = ""
            elif re.match(self.reg_comment_pattern[17], string[index:]):
                #//0x250
                match = re.match(self.reg_comment_pattern[17], string[index:])
                # print( match.group(1))
                member['addr_offset'] = match.group(1)
                member['init_value'] = ""
                member['init_value_type'] = ""
                member['description'] = ""
            else:
                member['addr_offset'] = ""
                member['init_value'] = ""
                member['init_value_type'] = ""
                member['description'] = ""
        else:
            member['addr_offset'] = ""
            member['init_value'] = ""
            member['init_value_type'] = ""
            member['description'] = ""
        
        return member

    def close(self):
        for f in self.files_handle:
            f.close()
        
        self.files_name = []
        self.files_handle = []
        self.files_content = []

if __name__ == '__main__':
    postproc = PostProcess()
    member = postproc.get_reg_comment('E:/learn_field/learn_lxml/castxml/bin/blc.h', '8')
    print(member['init_value'])
    member = postproc.get_reg_comment('E:/learn_field/learn_lxml/castxml/bin/blc.h', '9')
    print(member['init_value'])
    member = postproc.get_reg_comment('E:/learn_field/learn_lxml/castxml/bin/hdr.h', '10')
    print(member['init_value'])
    postproc.close()
    
