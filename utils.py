# _*_ coding:utf-8 _*_
__author__ = 'pb'
__date__ = '2017/6/21 15:46'
from django import forms
import re
import xlrd
from decimal import Decimal
import json


def obj_to_dict(obj):
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
    def __init__(self, f, data_type=None):
        self.import_data = xlrd.open_workbook(file_contents=f.read())
        self.data_type = data_type
        self.data = self.process()

    def process(self):
        table = self.import_data.sheets()[0]
        nrows = table.nrows  # 总行数
        colnames = table.row_values(0)  # 表头列名称数据
        lst = []
        if self.data_type is None:
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

        elif self.data_type == 'block_list':
            for rownum in range(1, nrows):  # 遍历全部数据行
                item = {}  # 刷新装本行数据的字典
                price = {}
                rows = table.row_values(rownum)  # 取出一行数据
                # 遍历这行数据
                for name, row in zip(colnames, rows):

                    # 遍历每个单元格数据
                    if name == 'weight' or name == 'price':
                        item[name] = '{0:.2f}'.format(row)
                    elif name == 'm3':
                        if row:
                            item[name] = '{0:.2f}'.format(row)
                        else:
                            item[name] = '{0:.2f}'.format(
                                float(item['long']) * float(item['width']) * float(
                                    item['high']) * 0.000001)
                    else:
                        item[name] = str(row).split('.')[0]
                lst.append(item)

        elif self.data_type == 'sheng':
            for rownum in range(1, nrows):  # 遍历全部数据行
                rows = table.row_values(rownum)  # 取出一行数据
                item = {}
                # 遍历这行数据
                for name, row in zip(colnames, rows):
                    # 遍历每个单元格数据
                    item[name] = str(row).split('.')[0]
                lst.append(item)

        elif self.data_type == 'city':
            for rownum in range(1, nrows):  # 遍历全部数据行
                rows = table.row_values(rownum)  # 取出一行数据
                item = {}
                # 遍历这行数据
                for name, row in zip(colnames, rows):
                    # 遍历每个单元格数据
                    item[name] = str(row).split('.')[0]
                lst.append(item)
        return lst


def default_decimal(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f'{obj} is not JSON')
