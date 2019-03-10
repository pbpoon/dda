# _*_ coding:utf-8 _*_
import datetime

from product.models import PackageListItem

__author__ = 'pb'
__date__ = '2017/6/21 15:46'
from django import forms
import re
import xlrd
from decimal import Decimal
import json


class StockOperateItem:
    def __init__(self, product, location, location_dest, piece, quantity, package_list):
        self.product = product
        self.location = location
        self.location_dest = location_dest
        self.piece = piece
        self.quantity = quantity
        self.package_list = package_list


class Package:
    def __init__(self, product, slabs):
        self.items = sorted(slabs, key=lambda x: (x.part_number, x.line))
        self.product = product

    def __iter__(self):
        for item in self.items:
            print(item)
            yield item

    def get_piece(self, number=None):
        items = self.items
        if number:
            items = [item for item in self.items if item.part_number == number]
        return len(items)

    def get_part_number(self, number=None):
        if number:
            items = {item.part_number for item in self.items if item.part_number == number}
        else:
            items = {item.part_number for item in self.items}
        return items

    def get_quantity(self, number=None):
        if number:
            quantity = sum(item.get_quantity() for item in self.items if item.part_number == number)
        else:
            quantity = sum(item.get_quantity() for item in self.items)
        return quantity

class PackageItem:
    def __init__(self, slab):
        self.part_number = slab.part_number
        self.line = slab.line
        # self. = slab.line



def obj_to_dict(obj, fields_lst=[]):
    return {q.name: getattr(obj, q.name) for q in obj._meta.fields if q.name in fields_lst}


def qs_to_dict(obj):
    if len(obj) > 1:
        lst = []
        for j in obj:
            lst.append({q.name: getattr(j, q.name) for q in j._meta.fields})
        return lst
    return {q.name: getattr(obj, q.name) for q in obj._meta.fields}


def str_to_list(str):
    s, r = '', ''
    try:
        s, *t, r = re.split(r'[\[,\s\]]\s', str)
    except Exception as e:
        t = str.split(',')
    if not t:
        return None
    if s:
        t.append(s.split('[')[1])
    if r:
        t.append(r.split(']')[0])
    return t


class AddExcelForm(forms.Form):
    file = forms.FileField(label='上传文件')


class ImportData:
    def __init__(self, f, data_type=None, data_format=None):
        self.import_data = xlrd.open_workbook(file_contents=f.read())
        self.data_type = data_type
        self.data = self.process()
        self.data_format = data_format

    def process(self):
        table = self.import_data.sheets()[0]
        nrows = table.nrows  # 总行数
        colnames = table.row_values(0)  # 表头列名称数据
        return getattr(self, self.data_type)(table, nrows, colnames)

    def package_list(self, table, nrows, colnames):
        lst = []
        for rownum in range(1, nrows):
            rows = table.row_values(rownum)
            item = {}
            for key, row in zip(colnames, rows):
                if not row:
                    if key == 'long' and key == 'high':
                        raise ValueError('长或宽没有数值!')
                if key == 'part_num':
                    if not row:
                        raise ValueError('有夹号没有数值！')
                    item[key] = str(row).split('.')[0]
                elif key == 'block_num':
                    if not row:
                        raise ValueError('有荒料编号没有数值！')
                    item[key] = str(row).split('.')[0]
                elif key == 'line_num':
                    if not row:
                        raise ValueError('有序号号没有数值！')
                    item[key] = int(row)
                else:
                    if row:
                        item[key] = '{0:.2f}'.format(row)
                    else:
                        item[key] = 0
            k1 = 0
            k2 = 0
            if item.get('kl1') and item.get('kh1'):
                k1 = Decimal(item['kl1']) * Decimal(item['kh1']) / 100000
            if item.get('kl2') and item.get('kh2'):
                k2 = Decimal(item['kl2']) * Decimal(item['kh2']) / 100000
            item['m2'] = '{0:.2f}'.format(
                Decimal(item['long']) * Decimal(item['high']) / 10000 + k1 + k2)
            lst.append(item)
        return lst

    def block_list(self, table, nrows, colnames):
        lst = []
        # if not self.data_type:
        #     self.data_type = {'updated': 'datetime'}
        for rownum in range(1, nrows):  # 遍历全部数据行
            item = {}  # 刷新装本行数据的字典
            price = {}
            rows = table.row_values(rownum)  # 取出一行数据
            # 遍历这行数据
            for name, row in zip(colnames, rows):

                # 遍历每个单元格数据
                if name in ('long', 'width', 'height'):
                    item[name] = int(row)
                elif name in ('weight', 'thick'):
                    try:
                        item[name] = Decimal('{0:.2f}'.format(row))
                    except Exception as e:
                        print(name, row, e)
                        item[name] = None
                elif name == 'updated':
                    updated = datetime.datetime.strptime(row, '%Y/%m/%d').date()
                    item[name] = updated
                else:
                    item[name] = str(row)
            print(name, row)
            lst.append(item)
        return lst

    def stock_list(self, table, nrows, colnames):
        lst = []
        # 导入的excel的pic_no和par_no用分列转换一下文本
        for rownum in range(1, nrows):  # 遍历全部数据行
            item = {}  # 刷新装本行数据的字典
            price = {}
            rows = table.row_values(rownum)  # 取出一行数据
            # 遍历这行数据
            for name, row in zip(colnames, rows):

                # 遍历每个单元格数据
                if name == 'pic':
                    if not row:
                        row = 1
                    item[name] = int(row)
                elif name in ('quantity', 'thick'):
                    try:
                        item[name] = Decimal('{0:.2f}'.format(row))
                    except Exception as e:
                        print(name, row, e)
                        item[name] = None
                elif name == 'updated':
                    updated = datetime.datetime.strptime(row, '%Y/%m/%d').date()
                    item[name] = updated
                else:
                    if row:
                        item[name] = str(row)
                    else:
                        item[name] = None
            print(name, row)
            lst.append(item)
        return lst

    def slab_list(self, table, nrows, colnames):
        lst = []
        # if not self.data_type:
        #     self.data_type = {'updated': 'datetime'}
        for rownum in range(1, nrows):  # 遍历全部数据行
            item = {}  # 刷新装本行数据的字典
            price = {}
            rows = table.row_values(rownum)  # 取出一行数据
            # 遍历这行数据
            for name, row in zip(colnames, rows):

                # 遍历每个单元格数据

                if name in ('m2', 'thick'):
                    try:
                        item[name] = Decimal('{0:.2f}'.format(row))
                    except Exception as e:
                        print(name, row, e)
                        item[name] = None
                elif name == 'entry_date':
                    # 一定要在excel文件用分列转换一下
                    updated = datetime.datetime.strptime(row, '%Y/%m/%d').date()
                    item[name] = updated
                else:
                    if row:
                        try:
                            item[name] = int(row)
                        except Exception as e:
                            item[name] = str(row)
                    else:
                        item[name] = None
            print(name, row)
            lst.append(item)
        return lst

    def address(self, table, nrows, colnames):
        lst = []
        for rownum in range(1, nrows):  # 遍历全部数据行
            rows = table.row_values(rownum)  # 取出一行数据
            item = {}
            # 遍历这行数据
            for name, row in zip(colnames, rows):
                # 遍历每个单元格数据
                item[name] = str(row).split('.')[0]
            lst.append(item)
        return lst

    def stock_trace(self, table, nrows, colnames):
        lst = []
        for rownum in range(1, nrows):  # 遍历全部数据行
            rows = table.row_values(rownum)  # 取出一行数据
            item = {}
            # 遍历这行数据
            for name, row in zip(colnames, rows):
                # 遍历每个单元格数据
                if name in ('part', 'pic'):
                    if row:
                        item[name] = int(row)
                    else:
                        item[name] = None
                elif name == 'quantity':
                    item[name] = Decimal('{0:.2f}'.format(row))
                elif name == 'date':
                    updated = datetime.datetime.strptime(row, '%Y/%m/%d').date()
                    item[name] = updated
                else:
                    item[name] = str(row).split('.')[0]
            lst.append(item)
        return lst


def default_decimal(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f'{obj} is not JSON')
