from django.http import JsonResponse
from django.shortcuts import render, redirect, render_to_response
from django.urls import reverse, reverse_lazy

from django.views import View
from django.views.generic import TemplateView, DetailView
from django.db.models import F
from datetime import datetime, timedelta
from django.contrib.auth.mixins import LoginRequiredMixin

from action.wechat import WxClient, WxJsSdkMixin
from sales.models import SalesOrder
from product.models import Block
from account.models import UserCollectBlock
from django.contrib.auth import get_user_model
from django.core import signing
from django.conf import settings
import hashlib


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'account/dashboard.html'

    def get_delay_ten_day_sales_order_count(self):
        # 收款账单
        # 销售单 开单后状态超期10天的
        # 最近 3张 生产单
        delay_ten_day = datetime.now() - timedelta(days=10)
        delay_sales_order = SalesOrder.objects.annotate(delay=datetime.now() - F('date')
                                                        ).filter(date__lte=delay_ten_day,
                                                                 state='confirm').count()
        return delay_sales_order

    def get_context_data(self, **kwargs):
        kwargs['object'] = self.request.user
        my_sales_order = SalesOrder.objects.filter(handler=self.request.user)
        kwargs['my_sales_order_count'] = my_sales_order.count()
        kwargs['my_sales_order_confirm_count'] = my_sales_order.filter(state='confirm').count()
        kwargs['my_sales_order_done_count'] = my_sales_order.filter(state='done').count()
        kwargs['delay_ten_day_sales_order_count'] = self.get_delay_ten_day_sales_order_count()
        return kwargs


class CollectBlockUpdateView(LoginRequiredMixin, View):

    def post(self, *args, **kwargs):
        inside = ''
        collect_block_id = kwargs.get('pk')
        collect_block_id = int(collect_block_id)
        if collect_block_id:
            try:
                collect_block = self.request.user.collect_block
            except Exception as e:
                from account.models import UserCollectBlock
                collect_block = UserCollectBlock.objects.create(user=self.request.user)
            lst = collect_block.block_list
            if lst is None:
                lst = []
            if collect_block_id not in lst:
                lst.append(collect_block_id)
                self.request.user.collect_block.block_list = lst
                self.request.user.collect_block.save()
                inside = 'yes'
                msg = '收集成功'
            else:
                lst.remove(collect_block_id)
                self.request.user.collect_block.block_list = lst
                self.request.user.collect_block.save()
                inside = 'no'
                msg = '从收集中移除'
        return JsonResponse({'state': 'ok', 'inside': inside, 'msg': msg})


class UserCollectBlockListMixin(WxJsSdkMixin, TemplateView):
    template_name = 'account/coolect_block_list.html'
    app_name = 'zdzq_main'
    blocks = None
    path = None

    def get_js_sdk_url(self):
        # return reverse_lazy('collect_block_share', kwargs={'string': self.path})
        #
        return f'{settings.DEFAULT_DOMAINS}{self.request.path}'

    def get_js_sdk_link(self):
        path = reverse_lazy('collect_block_share', kwargs={'string': self.path})
        return f'{settings.DEFAULT_DOMAINS}{path}'

    def get_js_sdk_title(self):
        return '云浮宏建石材现货推荐(%s)' % datetime.now().strftime('%Y-%m-%d')

    def get_js_sdk_desc(self):
        block_names = []
        if not self.blocks:
            return '颗颗精选'
        for block in self.blocks:
            for p in block.products.all():
                if p.type == 'semi_slab':
                    continue
                if p.stock.exists():
                    block_names.append(str(p))
        if len(block_names) > 6:
            block_names = block_names[:7]
            block_names.append('...')
        html = ','.join(block_names) if block_names else ''
        return '颗颗精选:%s' % html

    def get_context_data(self, **kwargs):
        try:
            collect_block_list = self.request.user.collect_block.block_list
        except Exception as e:
            obj = UserCollectBlock.objects.create(user=self.request.user)
            collect_block_list = obj.block_list
        if collect_block_list:
            blocks = Block.objects.filter(id__in=collect_block_list)
            string = signing.dumps({'collect_block_list': collect_block_list, 'user': self.request.user.id})
            self.path = string
            self.blocks = blocks
            kwargs.update({'object_list': blocks, 'share_url': self.path})
        return super().get_context_data(**kwargs)

    def post(self, *args, **kwargs):
        try:
            self.request.user.collect_block.block_list = []
            self.request.user.collect_block.save()
        except Exception as e:
            obj = UserCollectBlock.objects.create(user=self.request.user)
        return redirect(reverse('collect_block_list'))


class UserCollectBlockListView(LoginRequiredMixin, UserCollectBlockListMixin):
    pass


class CollectBlockShareMixin(UserCollectBlockListMixin):
    template_name = 'account/coolect_block_list.html'
    share_data = None

    def dispatch(self, request, *args, **kwargs):
        string = kwargs.get('string')
        if string:
            try:
                self.share_data = signing.loads(string)
                return super().dispatch(request, *args, **kwargs)
            except Exception as e:
                print(e)
        return render_to_response("404.html", {})


class CollectBlockPhotoListView(CollectBlockShareMixin):
    template_name = 'account/coolect_block_photo_list.html'

    def get_context_data(self, **kwargs):
        blocks = Block.objects.filter(id__in=self.share_data['collect_block_list'])
        user = get_user_model().objects.get(pk=self.share_data['user'])
        kwargs.update({'object_list': blocks, 'share_user': user})
        return super(UserCollectBlockListMixin,self).get_context_data(**kwargs)
