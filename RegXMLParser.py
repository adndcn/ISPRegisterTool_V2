from lxml import etree
import sys
import DocFactory
import PostProcess
import re


class RegXMLParser:
    def __init__(self, xml_file):
        self.xml_file = xml_file
        self.tree = etree.parse(xml_file)
        self.postproc = PostProcess.PostProcess()
        self.option = {'Little Endian': False, 'Byte Expand': True, 'Remove Reserved': True}
    
    def get_struct_element(self):
        xpath = '//Struct'
        return self.tree.xpath(xpath)

    def get_struct_name_by_id(self, id):
        '''get struct name by id string like '_13'...
        return: struct name(string)
        '''
        xpath = '//*[@type=\'%s\']'%(id)
        struct_name = self.tree.xpath(xpath)[0].attrib['name']
        return struct_name
    
    def get_element_by_id(self, id):
        xpath = '//*[@id=\'%s\']'%(id)
        element = self.tree.xpath(xpath)[0]
        return element

    def get_element_by_name(self, name):
        xpath = '//*[@name=\'%s\']'%(name)
        elem = self.tree.xpath(xpath)[0]
        return elem
    
    def get_struct_member(self, elem):
        '''get struct member from Element
        return: member Element list 
        '''
        member_id_lst = elem.attrib['members'].split(' ')
        member_element_list = []
        for id in member_id_lst:
            xpath = '//*[@id=\'%s\']'%(id)
            field = self.tree.xpath(xpath)[0]
            member_element_list.append(field)
        return member_element_list
    
    def get_element_by_type(self, type):
        xpath = '//*[@type=\'%s\']'%(type)
        elem = self.tree.xpath(xpath)
        return elem
    
    def recurse_cal_size(self, field_elem):
        field_type = field_elem.attrib['type']
        xpath = '//*[@id=\'%s\']'%(field_type)
        elem = self.tree.xpath(xpath)[0]
        size = 0

        if elem.tag == 'Typedef':
            size = self.recurse_cal_size(elem)
        elif elem.tag == 'FundamentalType':
            return int(elem.attrib['size'])
        elif elem.tag == 'ArrayType':
            size = (int(elem.attrib['max'])+1)*self.recurse_cal_size(elem)
        elif elem.tag == 'PointerType':
            return 32
        elif elem.tag == 'Struct':
            size = int(elem.attrib['size'])
        return size
    
    def is_array_elem(self, elem):
        if elem.tag == 'ArrayType':
            return True
        else:
            return False
    
    def recurse_array_field(self, array_elem, lst):
        num = int(array_elem.attrib['max'])+1
        lst.append(num)
        if self.is_array_elem(self.get_element_by_id(array_elem.attrib['type'])):
            self.recurse_array_field(self.get_element_by_id(array_elem.attrib['type']), lst)

    def get_array_list(self, field_elem):
        elem = self.get_element_by_id(field_elem.attrib['type'])
        if not self.is_array_elem(elem):
            return []
        else:
            lst = []
            self.recurse_array_field(elem, lst)
            return lst
    
    def analyze_member_element_list(self, member_element_list):
        '''analyze member_element_list
        '''
        members = []
        for (i, elem) in enumerate(member_element_list):
            members.append(self.analyze_member_element(elem))
        return members
    
    def get_basesize(self, element):
        if element.tag == 'FundamentalType':
            return int(element.attrib['size'])
        elif element.tag == 'Struct':
            return int(element.attrib['size'])
        elif element.tag == 'PointerType':
            return 32
        else:
            return self.get_basesize(self.get_element_by_id(element.attrib['type']))
    
    def get_basetype(self, element):
        if element.tag == 'FundamentalType':
            return 'FundamentalType'
        elif element.tag == 'Struct':
            return 'Struct'
        elif element.tag == 'PointerType':
            return 'PointerType'
        else:
            return self.get_basetype(self.get_element_by_id(element.attrib['type']))
    
    def get_filename_by_id(self, file_id):
        xpath = '//*[@id=\'%s\']'%(file_id)
        filename = self.tree.xpath(xpath)[0].attrib['name']
        return filename
    
    def analyze_member_element(self, elem):
        '''analyze member
        '''
        member = {}
        member["id"] = elem.attrib['id']
        member["line_number"] = elem.attrib['line']
        member["name"] = elem.attrib['name']
        member["offset"] = elem.attrib['offset']
        member["array_list"] = self.get_array_list(elem)
        member["cal_size"] = self.recurse_cal_size(elem)
        member["file"] = self.get_filename_by_id(elem.attrib['file'])
        member["base_size"] = self.get_basesize(elem)
        proc = self.postproc.get_reg_comment(member["file"], member["line_number"])
        member['addr_offset'] = proc['addr_offset']
        member['init_value'] = proc['init_value']
        member['init_value_type'] = proc['init_value_type']
        member['description'] = proc['description']
        member['type'] = self.get_basetype(elem)
        return member
    
    def _GetValueList(self, value_string):
        temp_values = re.split("\W", value_string)
        valueList = []
        for temp_v in temp_values:
            if temp_v != "":
                if 'u' in temp_v:
                    temp_v = temp_v[: temp_v.find('u')]
                valueList.append(temp_v)
        return valueList
    
    def _write(self, address, name, value, description, base_size, out):
        if self.option['Byte Expand']:
            if base_size//8 == 8:
                if self.option['Little Endian']:
                    postfix = ["[7:0]", "[15:8]", "[23:16]", "[31:24]", "[39:32]", "[47:40]", "[55:48]", "[63:56]"]
                    v = [value&0xff, (value>>8)&0xff, (value>>16)&0xff, (value>>24)&0xff, (value>>32)&0xff, (value>>40)&0xff, (value>>48)&0xff, (value>>56)&0xff]
                else:
                    postfix = ["[63:56]", "[55:48]", "[47:40]", "[39:32]", "[31:24]", "[23:16]", "[15:8]", "[7:0]"]
                    v = [(value>>56)&0xff, (value>>48)&0xff, (value>>40)&0xff, (value>>32)&0xff, (value>>24)&0xff, (value>>16)&0xff, (value>>8)&0xff, value&0xff]
                for j in range(8):
                    out.write(address + j, name+postfix[j], 8, v[j], description)
            elif base_size//8 == 4:
                if self.option['Little Endian']:
                    postfix = ["[7:0]", "[15:8]", "[23:16]", "[31:24]"]
                    v = [value&0xff, (value>>8)&0xff, (value>>16)&0xff, (value>>24)&0xff]
                else:
                    postfix = ["[31:24]", "[23:16]", "[15:8]", "[7:0]"]
                    v = [(value>>24)&0xff, (value>>16)&0xff, (value>>8)&0xff, value&0xff]
                for j in range(4):
                    out.write(address + j, name+postfix[j], 8, v[j], description)
            elif base_size//8 == 2:
                if self.option['Little Endian']:
                    postfix = ["[7:0]", "[15:8]"]
                    v = [value&0xff, (value>>8)&0xff]
                else:
                    postfix = ["[15:8]", "[7:0]"]
                    v = [(value>>8)&0xff, value&0xff]
                for j in range(2):
                    out.write(address + j, name+postfix[j], 8, v[j], description)
            else:
                out.write(address, name, base_size, value, description)
        else:
            out.write(address, name, base_size, value, description)
    
    def _str2int(self, value_str):
        if '0x' in value_str:
            if 'u' in value_str:
                value_int = int(value_str[:value_str.find('u')], 16)
            else:
                value_int = int(value_str, 16)
        elif '' == value_str:
            value_int = 0
        else:
            if 'u' in value_str:
                value_int = int(value_str[:value_str.find('u')])
            else:
                value_int = int(value_str)
        
        return value_int

    def write(self, prefix, address, member, out):
        # if self.option['Byte Expand'] == True:
        if member['array_list'] == []:
            value = self._str2int(member['init_value'])
            self._write(address, prefix+member['name'], value, member['description'], member['base_size'], out)
        else:
            length = len(member['array_list'])
            current_index = [0]*length
            total = 1
            for i in member['array_list']:
                total = total*i
            if member['init_value_type'] == "array":
                if '...' in member['init_value']:
                    value = self._str2int(member['init_value'].strip('...'))
                    
                    for i in range(total):
                        addr = address + member['base_size']*i//8
                        name = member['name']+self._ListToString(current_index)
                        self._write(addr, prefix + name, value, member['description'], member['base_size'], out)
                        self._add_array_list(member['array_list'], current_index, -1)
                else:
                    value = 0
                    value_list = self._GetValueList(member['init_value'])
                    for i in range(total):
                        addr = address + member['base_size']*i//8
                        name = member['name']+self._ListToString(current_index)

                        if i < len(value_list):
                            current_value = value_list[i]
                            value = self._str2int(current_value)
                        self._write(addr, prefix+name, value, member['description'], member['base_size'], out)
                        self._add_array_list(member['array_list'], current_index, -1)
            else:
                length = len(member['array_list'])
                current_index = [0]*length
                total = 1
                for i in member['array_list']:
                    total = total*i
                for i in range(total):
                    addr = address + member['base_size']*i//8
                    name = member['name']+self._ListToString(current_index)
                    self._write(addr, prefix + name, 0, member['description'], member['base_size'], out)
                    self._add_array_list(member['array_list'], current_index, -1)
    
    def recurse_write(self, prefix, elem, base_addr, out):
        if elem.tag == 'Typedef':
            # print('Typedef ', elem.attrib['id'])
            self.recurse_write(prefix, self.get_element_by_id(elem.attrib['type']), base_addr, out)
        elif elem.tag == 'Struct':
            print('Struct ', elem.attrib['id'])
            member_element_list = self.get_struct_member(elem)
            for e in member_element_list:
                m = self.analyze_member_element(e)
                if self.option['Remove Reserved'] == True and 'reserve' in m['name'].lower():
                    pass
                else:
                    address = base_addr + int(m['offset'])//8
                    if m['array_list'] == [] and m['type'] != 'Struct':
                        self.write(prefix, address, m, out)
                    elif m['array_list'] == [] and m['type'] == 'Struct':
                        self.recurse_write(prefix+m['name']+'.', self.get_element_by_id(e.attrib['type']), address, out)
                    elif m['array_list'] != [] and m['type'] != 'Struct':
                        self.write(prefix, address, m, out)
                    else:#m['array_list'] != [] and m['type'] == 'Struct':
                        length = len(m['array_list'])
                        current_index = [0]*length
                        total = 1
                        for i in m['array_list']:
                            total = total*i
                        for i in range(total):
                            address = address + m['base_size']*i//8
                            self.recurse_write(prefix + m['name'] + self._ListToString(current_index) + '.', self.get_element_by_id(e.attrib['type']), address, out)
                            self._add_array_list(m['array_list'], current_index, -1)
                # print(self.analyze_member_element(e))
                # self.recurse_write(self.get_element_by_id(e.attrib['type']), address, out)
        elif elem.tag == 'ArrayType':
            # print(elem.tag, ' ', elem.attrib['id'])
            self.recurse_write(prefix, self.get_element_by_id(elem.attrib['type']), base_addr, out)
        else:
            # print(elem.tag, ' ', elem.attrib['id'])
            pass
        
    def _ListToString(self, lst):
        length = len(lst)
        if length > 0:
            lst_string = ''
            for l in lst:
                lst_string += '[%d]'%(l)
            return lst_string
        else:
            return ''
    
    def _add_array_list(self, array_list, current_index, i):
        if -i <= len(array_list):
            current_index[i] = current_index[i] + 1
            if current_index[i] == array_list[i]:
                current_index[i] = 0
                i = i-1
                self._add_array_list(array_list, current_index, i)

    def write_array(self, elem, elem_desp, address, out):
        length = len(elem_desp['array_list'])
        current_index = [0]*length
        total = 1
        for i in elem_desp['array_list']:
            total = total*i
        for i in range(total):
            self._add_array_list(elem_desp['array_list'], current_index, -1)


    def file_write(self, elem, base_addr, out, expand_title):
        if expand_title:
            member_element_list = self.get_struct_member(elem)
            for e in member_element_list:
                # print('dabiaoti: ', e.attrib['name'])
                m = self.analyze_member_element(e)
                if self.option['Remove Reserved'] == True and 'reserve' in m['name'].lower():
                    pass
                else:
                    if m['array_list'] == []:
                        address = base_addr + int(m['offset'])//8
                        out.add_header(m['name'])
                        self.recurse_write('', self.get_element_by_id(e.attrib['type']), address, out)
                    else:
                        address = base_addr + int(m['offset'])//8
                        length = len(m['array_list'])
                        current_index = [0]*length
                        total = 1
                        for i in m['array_list']:
                            total = total*i
                        for i in range(total):
                            address = address + m['base_size']*i//8
                            out.add_header(m['name']+self._ListToString(current_index))
                            self._add_array_list(m['array_list'], current_index, -1)
                            self.recurse_write('', self.get_element_by_id(e.attrib['type']), address, out)
        else:
            name = self.get_struct_name_by_id(elem.attrib['id'])
            if self.option['Remove Reserved'] == True and 'reserve' in name.lower():
                pass
            else:
                out.add_header(name)
                self.recurse_write('', elem, base_addr, out)

        
        self.postproc.close()

    

if __name__ == '__main__':
    parser = RegXMLParser('E:/learn_field/learn_lxml/result.xml')
    # print(parser.get_struct_element())
    # for s in parser.get_struct_element():
    #     print(s.attrib['id'])
    # print(parser.get_struct_name_by_id('_15'))
    # print(parser.get_struct_member(parser.get_struct_element()[1]))
    # elem_list = parser.get_struct_member(parser.get_struct_element()[1])
    # size = parser.recurse_cal_size(parser.get_element_by_id('_40'))
    # print(size)

    # print(parser.get_array_list(parser.get_element_by_id('_35')))

    # print(parser.analyze_member_element_list([parser.get_element_by_id('_41')]))

    file = DocFactory.DocFactory.doc_generator('out.txt')
    file.open()
    parser.file_write(parser.get_element_by_id('_19'), 0x8000, file, False)
    file.close()
    # print(parser.get_basesize(parser.get_element_by_id('_40')))
    