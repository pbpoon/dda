#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/1/13
from django.db.models import F
from django.http import HttpResponse
from django.views.generic import FormView
from django.core.exceptions import ObjectDoesNotExist
from comment.models import Comment
from product.models import Block, Category, Quarry, Batch, Product, Slab
from public.utils import ImportData
from public.forms import AddExcelForm
from stock.models import OriginalStockTrace
from .models import Partner, Province, City
from django.db import transaction


class ImportPartnerView(FormView):
    """
    导入省份，城市数据
    """
    data_type = 'city'
    template_name = 'form.html'
    form_class = AddExcelForm

    @transaction.atomic()
    def form_valid(self, form):
        f = form.files.get('file')

        model = Province if self.data_type == 'address' else City
        import_data = ImportData(f, data_type='address').data
        companys = self.format_to_company(import_data)
        for i in companys:
            data = {'name': i['company'],
                    'is_company': True,
                    'province': self.get_province(i),
                    'city': self.get_city(i),
                    'phone': i['phone'],
                    'type': 'customer',
                    'entry': self.request.user
                    }
            Partner.objects.create(**data)
        for i in import_data:
            data = {'name': i['name'],
                    'company': self.get_company(i),
                    'province': self.get_province(i),
                    'city': self.get_city(i),
                    'phone': i['phone'],
                    'type': 'customer',
                    'entry': self.request.user
                    }
            # data = {'id': i['id'],
            #         'code': i['provinceID'],
            #         'name': i['province']}
            Partner.objects.get_or_create(**data)

        return HttpResponse('0k')

    def get_province(self, i):
        if i['province']:
            return Province.objects.get(pk=i['province'])
        return None

    def get_city(self, i):
        if i['city']:
            return City.objects.get(pk=i['city'])
        return None

    def get_company(self, c):
        cc = None
        if c['company']:
            cc = Partner.objects.filter(is_company=True, name=c['company'])[0]
        return cc

    def format_to_company(self, data):
        return [i for i in data if i['company']]

class ImportStockTraceView(FormView):
    """
    导入 stock trace，城市数据
    """
    data_type = 'stock_trace'
    template_name = 'form.html'
    form_class = AddExcelForm

    @transaction.atomic()
    def form_valid(self, form):
        f = form.files.get('file')

        model = Province if self.data_type == 'stock_trace' else City
        import_data = ImportData(f, data_type='stock_trace').data
        lst = []
        for i in import_data:
            data = {'block': self.get_block(i),
                    'address': i['address'],
                    'date': i['date'],
                    'part': i['part'],
                    'piece': i['pic'],
                    'quantity': i['quantity'],
                    'uom': i['unit'],
                    'stock_trace': i['stock_trace'],
                    }
            # data = {'id': i['id'],
            #         'code': i['provinceID'],
            #         'name': i['province']}
            ost = OriginalStockTrace(**data)
            lst.append(ost)
        OriginalStockTrace.objects.bulk_create(lst)

        return HttpResponse('0k')

    def get_block(self, i):
        return Block.objects.get(name=i['block_no'])

    def get_city(self, i):
        if i['city']:
            return City.objects.get(pk=i['city'])
        return None

    def get_company(self, c):
        cc = None
        if c['company']:
            cc = Partner.objects.filter(is_company=True, name=c['company'])[0]
        return cc

    def format_to_company(self, data):
        return [i for i in data if i['company']]


class ImportBlockView(FormView):
    """
    导入 荒料 数据
    """
    data_type = 'block_list'
    template_name = 'form.html'
    form_class = AddExcelForm

    @transaction.atomic()
    def form_valid(self, form):
        f = form.files.get('file')

        model = Block
        import_data = ImportData(f, data_type='block_list').data

        c_parent = Category.objects.create(name='大理石')
        category = Category.objects.create(name='浅啡网', parent=c_parent)

        self.create_quarry(import_data)
        self.create_batch(import_data)

        for i in import_data:
            data = {'name': i['block'],
                    'batch': self.get_batch(i),
                    'category': category,
                    'quarry': self.get_quarry(i),
                    'weight': i['weight'],
                    'long': i['long'],
                    'width': i['width'],
                    'height': i['height'],
                    }

            block, _ = Block.objects.get_or_create(**data)
            if i['ps']:
                content = '%s(%s)'%(i['ps'], '从pccs旧系统导入')
                block.comments.create(content=i['ps'], user=self.request.user)

        for j in import_data:
            type = j['block_type']
            thickness = j.get('thick', None)
            name = j['block']
            product = Block.create_product(type, {}, name, thickness)
            print(product)

        return HttpResponse('0k')

    def get_batch(self, i):
        return Batch.objects.get(name=i['batch'])

    def get_quarry(self, i):
        return Quarry.objects.get(name=i['quarry'])

    def create_quarry(self, data):
        set_lst = {i['quarry'] for i in data if i['quarry']}
        quarry_lst = []
        for name in set_lst:
            quarry = Quarry(name=name)
            quarry_lst.append(quarry)
        Quarry.objects.bulk_create(quarry_lst)

    def create_batch(self, data):
        set_lst = {i['batch'] for i in data if i['batch']}
        batch_lst = []
        for name in set_lst:
            batch = Batch(name=name)
            batch_lst.append(batch)
        Batch.objects.bulk_create(batch_lst)


class ImportStockView(FormView):
    """
    导入 库存 数据
    第一次是荒料和板材
    需要导入第二次的毛板库存
    """
    template_name = 'form.html'
    form_class = AddExcelForm

    @transaction.atomic()
    def form_valid(self, form):
        from stock.models import Stock
        f = form.files.get('file')

        import_data = ImportData(f, data_type='stock_list').data

        self.create_address(import_data)

        for i in import_data:
            # if i['block_no'] == '6523':
            #     continue
            data = {'product': self.get_product(i),
                    'location': self.get_location(i),
                    'quantity': i['quantity'],
                    'uom': i['unit'],
                    'piece': i['piece'],
                    'updated': i['updated'],
                    }
            stock = Stock.objects.filter(product=data['product'], location=data['location'])
            if stock:
                stock.update(quantity=F('quantity') + data['quantity'], piece=F('piece') + data['piece'])
                continue
            else:
                stock = Stock.objects.create(**data)
            print(stock.product, stock.piece, stock.quantity, stock.uom)

        return HttpResponse('0k')

    def get_product(self, data):
        return Block.create_product(type=data['type'], defaults={}, name=data['block_no'], thickness=data['thick'])
        # try:
        #     Product.objects.filter(block__name=data['block_no'], type=data['type'], thickness=data['thick'])[0]
        # except ObjectDoesNotExist:
        #     raise ValueError(data['block_no'], data['type'], data['thick'], '没有产品')

    def get_location(self, data):
        from stock.models import Warehouse
        return Warehouse.objects.get(name=data['address']).get_main_location()

    def create_address(self, data):
        from stock.models import Warehouse
        set_lst = {i['address'] for i in data if i['address']}
        wh_lst = []
        for name in set_lst:
            if not Warehouse.objects.filter(name=name).exists():
                wh = Warehouse(name=name, is_production=True, code=name)
                wh.save()
                print(wh.get_main_location())
            else:
                pass
        # Warehouse.objects.bulk_create(wh_lst)


class ImportSlabView(FormView):
    """
    导入 slab 数据
    """
    template_name = 'form.html'
    form_class = AddExcelForm

    @transaction.atomic()
    def form_valid(self, form):
        f = form.files.get('file')

        import_data = ImportData(f, data_type='slab_list').data

        # self.create_address(import_data)
        slab_list = []
        for i in import_data:
            data = {'long': i['long'],
                    'height': i['hight'],
                    'kl1': i['kl1'],
                    'kl2': i['kl2'],
                    'kh1': i['kh1'],
                    'kh2': i['kh2'],
                    'part_number': i['part_no'],
                    'line': i['pic_no'],
                    'stock': self.get_stock(i),
                    }
            slab = Slab(**data)
            slab_list.append(slab)
        Slab.objects.bulk_create(slab_list)

        return HttpResponse('0k')

    # def create_address(self, data):
    #     from stock.models import Warehouse
    #     set_lst = {i['address'] for i in data if i['address']}
    #     wh_lst = []
    #     for name in set_lst:
    #         if not Warehouse.objects.filter(name=name).exists():
    #             wh = Warehouse(name=name, is_production=True, code=name)
    #             wh.save()
    #             print(wh.get_main_location())
    #         else:
    #             pass

    def get_product(self, data):
        return Block.create_product(type='slab', defaults={}, name=data['block_no'], thickness=data['thick'])
        # try:
        #     return Product.objects.filter(block__name=data['block_no'], type='slab', thickness=data['thick'] )[0]
        # except ObjectDoesNotExist:
        #     raise ValueError(data['block_no'], data['type'], data['thick'], '没有产品')

    def get_location(self, data):
        from stock.models import Warehouse
        return Warehouse.objects.get(name=data['address']).get_main_location()

    def get_stock(self, data):
        from stock.models import Stock
        product = self.get_product(data)
        location = self.get_location(data)
        stock, _ = Stock.objects.get_or_create(product=product, location=location, defaults={'piece':1, 'quantity':1, 'uom':'m2'})
        return stock
