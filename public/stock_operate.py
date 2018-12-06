#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/7

from stock.models import Stock, StockTrace
from product.models import Slab
from django.db import transaction


class StockOperate:
    """只有location的is_virtual=True是才写入stock
        日后slab有一个字段链接到stock，用于记载slab的product的stock
        最终写入stock要做如下：
        入库：
            原库有可能是实体库：供应商的内部库位，有可能是供应商或客户（退货单时）的is_virtual库位
                1：检查原库位库存（如果原库位是is_virtual，就不检查原库位可用库存）
                2：写入StockTrace和更新stock，
        出库：
            原库位一般情况是自己的库位，有可能是供应商的内部库位，不可能是is_virtual
            目标库必须为：is_virtual
                1：检查库存
                2：写入StockTrace和更新stock，
        移库：
            原库及目标库位都必须是内部库位
            可出库时填号单据，入库时确认
                1：检查库存
                2：写入StockTrace和更新stock，
        """

    # def __init__(self, request, order, items, location, location_dest):
    def __init__(self, request, order, items):
        """
        Args:
            order: object, 对应的订单object，这是一个content_type
            items: 对应的订单items
            location: 原库位
            location_dest: 目标库位
        """
        self.request = request
        self.stock_model = Stock
        self.trace_model = StockTrace
        self.slab_model = Slab
        self.order = order
        self.items = items
        # self.location = location
        # self.location_dest = location_dest

    def _get_stock(self, product, location, slabs=None, check_in=False):
        # 取得库存的记录
        return Stock._get_stock(product, location, slabs, check_in=check_in)

    def get_available(self, product, location, slabs=None):
        """
        Args:
            product: object产品
            location: object库位
            slabs: questset板材

        Returns:元祖，（件，数量）

        """
        return Stock.get_available(product=product, location=location, slabs=slabs)

    def update_slab_stock(self, slabs, stock=None, check_in=False, update_reserve=False):
        # 更新板材的库位
        if check_in:
            slabs.update(stock=stock)
            return True
        slabs.update(stock=None)
        return True

    def check_in_stock(self, product, location, piece, quantity, slabs=None):
        # 入库
        available = self._get_stock(product=product, location=location, check_in=True)
        if available:
            available[0].piece += piece
            available[0].quantity += quantity
            available[0].save()
            stock = available[0]
        else:
            stock = self.stock_model.objects.create(product=product, piece=piece, quantity=quantity,
                                                    uom=product.uom, location=location)
        if slabs:
            return self.update_slab_stock(slabs=slabs, stock=stock, check_in=True)
        return True

    def check_out_stock(self, product, location, piece, quantity, slabs=None):
        # 出库
        piece, quantity = list(map(abs, [piece, quantity]))
        # # 如果可以的件数大于需求的件数就继续执行
        available = self._get_stock(product=product, location=location, slabs=slabs)
        if available:
            try:
                for a in available:
                    max_piece, max_quantity = min((a.piece - a.reserve_piece), piece), \
                                              min((a.quantity - a.reserve_quantity), quantity)
                    a.piece -= max_piece
                    a.quantity -= max_quantity
                    piece -= max_piece
                    quantity -= max_quantity
                    if a.piece == 0:
                        a.delete()
                    else:
                        # 修正毛板的库存方数
                        if a.product.type == 'semi_slab':
                            a.quantity = a.piece * a.product.semi_slab_single_qty
                        a.save()
                    if piece == 0:
                        break
            except Exception as e:
                max_piece, max_quantity = min((available.piece - available.reserve_piece), piece), \
                                          min((available.quantity - available.reserve_quantity), quantity)
                available.piece -= max_piece
                available.quantity -= max_quantity
                piece -= max_piece
                quantity -= max_quantity
                if available.piece == 0:
                    available.delete()
                else:
                    available.save()
            if slabs:
                return self.update_slab_stock(slabs=slabs)
            return True
        return False

    def update_available(self, product, location, piece, quantity, slabs=None):
        if product.type == 'slab':
            if slabs is None:
                return False
        if location.is_virtual:
            # '库位为虚拟库位，不可查！
            return False
        if piece > 0:  # 入库
            return self.check_in_stock(product=product, location=location, piece=piece, quantity=quantity,
                                       slabs=slabs)
        else:  # 出库
            return self.check_out_stock(product=product, location=location, piece=piece, quantity=quantity,
                                        slabs=slabs)

    def update_reserve(self, product, location, piece, quantity, slabs=None):
        # # 如果可以的件数大于需求的件数就继续执行
        available = self._get_stock(product=product, location=location, slabs=slabs)
        if available:
            for a in available:
                if piece > 0:
                    # 锁库
                    max_piece, max_quantity = min((a.piece - a.reserve_piece), piece), \
                                              min((a.quantity - a.reserve_quantity), quantity)
                    a.reserve_piece += max_piece
                    a.reserve_quantity += max_quantity
                    piece -= max_piece
                    quantity -= max_quantity
                    a.save()
                    if piece == 0:
                        if slabs:
                            slabs.update(is_reserve=True)
                        return True
                else:
                    # 解库
                    max_piece, max_quantity = min((a.piece - a.reserve_piece), abs(piece)), \
                                              min((a.quantity - a.reserve_quantity), abs(quantity))
                    a.reserve_piece -= max_piece
                    a.reserve_quantity -= max_quantity
                    piece += max_piece
                    quantity += max_quantity
                    a.save()
                    if piece == 0:
                        if slabs:
                            slabs.update(is_reserve=False)
                        return True
        return False

    def clean_items(self):
        # 循环检查item的product的需求是否超出可以数量,
        # 如果超出就记载日error list，用作message返回
        error = []
        for item in self.items:
            if not item.location.is_virtual:
                av_piece, av_quantity = self.get_available(product=item.product, location=item.location)
                if (av_piece - item.piece) < 0:
                    error.append('{product}#可以库存为:{av_piece}件/{av_quantity}{uom},超出需求{piece}件/{quantity}{uom}'.format(
                        product=item.product, av_piece=av_piece, av_quantity=av_quantity, piece=item.piece,
                        quantity=item.quantity, uom=item.product.uom))
        if error:
            return False, error
        return True, error

    @transaction.atomic()
    def reserve_stock(self, unlock=False):
        state = -1 if unlock else 1
        clean, error = self.clean_items()
        if clean:
            # 创建数据库事务保存点
            sid = transaction.savepoint()
            for item in self.items:
                if not item.location.is_virtual:
                    package_list = getattr(item, 'package_list', None)
                    slabs = Slab.objects.filter(
                        id__in=package_list.items.values_list('slab', flat=True)) if package_list else None
                    if not self.update_reserve(product=item.product, location=item.location, piece=state * item.piece,
                                               quantity=state * item.quantity, slabs=slabs):
                        break
            else:
                transaction.savepoint_commit(sid)
                return True, '成功锁定库存'
                # 回滚数据库到保存点
            transaction.rollback(sid)
            return False, '锁定库存失败'
        return False, error

    @transaction.atomic()
    def handle_stock(self):
        clean, error = self.clean_items()
        if clean:
            # 创建数据库事务保存点
            sid = transaction.savepoint()
            # 操作出库
            for item in self.items:
                if not item.location.is_virtual:
                    package_list = getattr(item, 'package_list', None)
                    slabs = Slab.objects.filter(
                        id__in=package_list.items.values_list('slab', flat=True)) if package_list else None
                    if not self.update_available(product=item.product, location=item.location, piece=-item.piece,
                                                 quantity=-item.quantity, slabs=slabs):
                        break
                # 操作入库
                if not item.location_dest.is_virtual:
                    package_list = getattr(item, 'package_list', None)
                    slabs = Slab.objects.filter(
                        id__in=package_list.items.values_list('slab', flat=True)) if package_list else None
                    if not self.update_available(product=item.product, location=item.location_dest,
                                                 piece=item.piece,
                                                 quantity=item.quantity, slabs=slabs):
                        break

            else:
                # 更新数据库
                transaction.savepoint_commit(sid)
                return True, '成功更新库存'
            # 回滚数据库到保存点
            transaction.rollback(sid)
            return False, '更新库存失败'
        return False, error
