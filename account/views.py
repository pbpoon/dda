from django.shortcuts import render
from django.views.generic import TemplateView
from django.db.models import F
from datetime import datetime, timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from sales.models import SalesOrder


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
