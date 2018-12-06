import math
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import decimal
from django.db import models
from django.urls import reverse

from mrp.models import MrpOrderAbstract, OrderItemBase
from product.models import Product
from public.fields import OrderField

# from stock.stock_operate import StockOperate

UOM_CHOICES = (('t', '吨'), ('m3', '立方'), ('m2', '平方'))
TYPE_CHOICES = (('block', '荒料'), ('semi_slab', '毛板'), ('slab', '板材'))
EXPENSE_BY_CHOICES = (('raw', '原材料项'), ('produce', '产品项'), ('all', '原料及产品'))


class ProductionType(models.Model):
    name = models.CharField('业务类型', max_length=30)
    expense_by = models.CharField('费用结算按', max_length=10, choices=EXPENSE_BY_CHOICES)
    raw_item_type = models.CharField('原材料类型', max_length=10, choices=TYPE_CHOICES, default='block')
    produce_item_type = models.CharField('产出品类型', max_length=10, choices=TYPE_CHOICES, default='block')
    activate = models.BooleanField('启用', default=False)

    class Meta:
        verbose_name = '生产业务类型明细'

    def get_absolute_url(self):
        return reverse('production_type_detail', args=[self.id])

    def get_update_url(self):
        return reverse('production_type_update', args=[self.id])

    def __str__(self):
        return self.name


class ProductionOrder(MrpOrderAbstract):
    order = OrderField(order_str='MO', blank=True, verbose_name='单号', default='New', max_length=20)
    production_type = models.ForeignKey(ProductionType, on_delete=models.CASCADE, verbose_name='业务类型',
                                        limit_choices_to={'activate': True})

    class Meta:
        verbose_name = '生产订单'

    def get_absolute_url(self):
        return reverse('production_detail', args=[self.id])

    def get_update_url(self):
        return reverse('production_update', args=[self.id])

    def get_create_item_url(self):
        return reverse('production_raw_item_create', args=[self.id])

    def get_location(self):
        return self.warehouse.get_main_location()

    def get_location_dest(self):
        return self.warehouse.get_production_location()


class ProductionOrderRawItem(OrderItemBase):
    order = models.ForeignKey('ProductionOrder', on_delete=models.CASCADE, related_name='items')
    piece = models.IntegerField('件', default=1, blank=True, null=True)
    quantity = models.DecimalField('数量', max_digits=5, decimal_places=2, null=True, blank=True)
    uom = models.CharField('计量单位', null=False, choices=UOM_CHOICES, max_length=10, default='t')
    price = models.DecimalField('单价', max_digits=8, decimal_places=2, blank=True, null=True)

    class Meta:
        verbose_name = '生产单原料行'

    def get_amount(self):
        if self.product.type == 'block':
            return self.get_m3() * self.price
        return 0

    def get_m3(self):
        return self.product.get_m3()

    def __str__(self):
        return str(self.product)

    # def get_available(self):
    #     stock = StockOperate()
    #     piece, quantity = stock.get_available(product=self.product, location=self.location)
    #     return piece, quantity

    # 估算毛板的出材率
    def semi_slab_single_qty(self):
        # 先取出对应的item的最小的厚度
        all_produces = self.produces.all()
        if not all_produces:
            return None
        all_produces_dict = {i.thickness: i.piece for i in all_produces}
        min_thickness = min_thickness_key = min(all_produces_dict.keys())
        # 把最小如果是1。5的就改成1。4，之后把厚度+0。43刀头的厚度
        min_thickness = decimal.Decimal(1.4) if min_thickness == 1.5 else min_thickness
        min_thickness += decimal.Decimal(0.43)
        # 用m3 x 厚度出材率计算出最小规格的总出材率
        m3 = self.product.get_m3()
        total_min_thickness_m2 = m3 * (decimal.Decimal(100) - min_thickness) / min_thickness
        total_min_piece = all_produces_dict[min_thickness_key]
        # 如果该荒料的规格厚度为多个，就用其他厚度x件数就算出该厚度为最小厚度的件数，
        # 用最小厚度添加计算出来的件数，最总计算出如果该料界最小厚度会有多少件数，最后用最小厚度的总估算平方数除以估算的总件，计算出单价平方数
        if len(all_produces) > 1:
            for i in all_produces:
                total_min_piece += math.ceil((i.thickness + decimal.Decimal(0.43) * i.piece / min_thickness))
        single_qty = total_min_thickness_m2 / total_min_piece
        return single_qty

    def update_produces_quantity(self):
        single_qty = self.semi_slab_single_qty()
        if single_qty:
            for p in self.produces.all():
                ProductionOrderProduceItem.objects.filter(pk=p.id).update(quantity=p.piece * single_qty)
                Product.objects.filter(pk=p.product.id).update(semi_slab_single_qty=single_qty)


class ProductionOrderProduceItem(OrderItemBase):
    order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE, related_name='produce_items',
                              verbose_name='对应界石单')
    raw_item = models.ForeignKey('ProductionOrderRawItem', on_delete=models.CASCADE, related_name='produces',

                                 verbose_name='原材料')
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, verbose_name='product', blank=True,
                                null=True)
    thickness = models.DecimalField('厚度规格', max_digits=5, decimal_places=2, blank=True, null=True)
    quantity = models.DecimalField('数量', decimal_places=2, max_digits=10, null=True, blank=True)
    price = models.DecimalField('单价', max_digits=8, decimal_places=2, help_text='立方单价', null=True, blank=True)
    draft_package_list = models.ForeignKey('product.DraftPackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                           verbose_name='草稿码单')
    package_list = models.ForeignKey('product.PackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                     verbose_name='码单')

    class Meta:
        verbose_name = '生产单成品行'
        # unique_together = ['thickness', 'raw_item']

    def get_location(self):
        return self.order.location_dest

    def get_location_dest(self):
        return self.order.location

    def save(self, *args, **kwargs):
        self.order = self.raw_item.order
        thickness = self.thickness or self.raw_item.product.thickness
        self.product = self.raw_item.product.create_product(type=self.order.production_type.produce_item_type,
                                                            thickness=thickness)
        if self.draft_package_list:
            self.package_list = self.draft_package_list.make_package_list(product=self.product)
            self.piece = self.package_list.get_piece()
            self.quantity = self.package_list.get_quantity()
            self.draft_package_list = None
        super().save(*args, **kwargs)


# 更新毛板平方数的
@receiver(post_save, sender=ProductionOrderProduceItem, dispatch_uid='dis')
def production_produce_item_post_save_update_produces_quantity(sender, **kwargs):
    instance = kwargs['instance']
    type = instance.order.production_type.produce_item_type
    if type == 'semi_slab':
        instance.raw_item.update_produces_quantity()
    elif type == 'slab':
        package_list = instance.package_list
        if package_list:
            instance.raw_item.piece = package_list.get_piece()
            instance.raw_item.quantity = package_list.get_quantity()
            instance.raw_item.save()


@receiver(post_delete, sender=ProductionOrderProduceItem, dispatch_uid='sid')
def production_produce_item_post_delete_update_produces_quantity(sender, **kwargs):
    instance = kwargs['instance']
    type = instance.order.production_type.produce_item_type
    if type == 'semi_slab':
        instance.raw_item.update_produces_quantity()
    elif type == 'slab':
        package_list = instance.package_list
        if package_list:
            instance.raw_item.piece = None
            instance.raw_item.quantity = None
            instance.raw_item.save()
