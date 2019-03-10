from datetime import datetime
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
#
# # Create your views here.
from django.urls import reverse
from django.views.generic.base import View
# from wechatpy import parse_message, create_reply
# from wechatpy.enterprise.client import WeChatClient
# from wechatpy.enterprise.crypto import WeChatCrypto
# from wechatpy.exceptions import InvalidSignatureException
# from wechatpy.replies import BaseReply
from wechatpy.enterprise import parse_message
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.enterprise.client import WeChatClient
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.replies import BaseReply, create_reply

from action.models import WxConf

from django.views.decorators.csrf import csrf_exempt

corp_id = 'wwb132fd0d32417e5d'


# EncodingAESKey = '3BQNStGMtbmLAiCnQlabHRtEL3qclhAL8XeZ9yM7K0e'
# token = 'ohsAdNB8d3DHdv8xQj8'
# wx_conf = WxConf(agent_id=corp_id)


class WechatBaseView(View):
    app_name = 'zdzq_main'
    # wx_conf = WxConf(app_name=app_name)
    # crypto = WeChatCrypto(wx_conf.Token, wx_conf.EncodingAESKey, wx_conf.corp_id)
    wx_data = {}

    def get_wx_conf(self):
        return WxConf(app_name=self.app_name)

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        wx_conf = self.get_wx_conf()
        self.crypto = WeChatCrypto(wx_conf.Token, wx_conf.EncodingAESKey, wx_conf.corp_id)

        self.wx_data['signature'] = request.GET.get('msg_signature', '')
        self.wx_data['timestamp'] = request.GET.get('timestamp', '')
        self.wx_data['nonce'] = request.GET.get('nonce', '')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        echo_str = request.GET.get('echostr', '')
        print(echo_str, 'get')
        try:
            echo_str = self.crypto.check_signature(
                echo_str=echo_str, **self.wx_data
            )
            print('ok', 'get')
        except InvalidSignatureException:
            echo_str = 'error'
            print('error', 'get')
        return HttpResponse(echo_str)

    # POST方式用于接受和返回请求
    def post(self, request, *args, **kwargs):
        reply = None
        print(request.body, 'post_request')
        msg = self.crypto.decrypt_message(request.body, **self.wx_data)
        # 判断消息类型，文本消息则调用reply_text进行处理
        msg = parse_message(msg)
        self.orign_msg = msg
        print(msg, 'post_msg')
        if msg.type == 'text':
            # reply = self.reply_text.do_reply(msg)
            reply = self.reply_text()
        elif msg.type == 'event':
            reply = self.reply_event()
            # pass
        else:
            pass
        # if not reply or not isinstance(reply, BaseReply):
        #     reply = create_reply('暂不支持您所发送的消息类型哟~ 回复“帮助”查看使用说明。', msg)

        response = self.crypto.encrypt_message(reply, self.wx_data['nonce'], self.wx_data['timestamp'])
        return HttpResponse(response)

    # def get_url(self,so):
    #     return "%s" % (self.request.build_absolute_uri(so.get_absolute_url()))

    # def get_title(self):
    #     title = "%s/金额：¥%s    [%s]" % (
    #         self.model._meta.verbose_name, self.object.amount, self.object.get_state_display())
    #     return title

    def get_items(self, so):
        print('get_items')
        html = '\n---------------------------------'
        for item in so.items.all():
            if html:
                html += '\n'
            html += '(%s) %s /%s夹/%s件/%s%s *¥%s' % (
                item.line, item.product, str(item.package_list.get_part()) if item.package_list else '',
                item.piece, item.quantity, item.uom, item.price)
        html += '\n---------------------------------\n'
        html += '合计：'
        print('item html', html)
        for key, item in so.get_total().items():
            html += '%s:%s %s件/%s%s\n' % (
                key, item['part'] if item.get('part') else '', item['piece'],
                item['quantity'], item['uom'])
        html += '\n金额：¥ %s' % so.amount
        return html

    def get_description(self, so):
        print('desc')
        html = '单号:%s\n' % so.order
        html += '\n客户:%s' % so.partner
        html += '\n销往:%s' % so.get_address()
        html += "\n订单日期:%s" % (datetime.strftime(so.date, "%Y/%m/%d"))
        html += "\n销售:%s" % so.handler
        now = datetime.now()
        print('ready get_items')
        html += '%s' % self.get_items(so)
        html += '\n操作:%s \n@%s' % (self.request.user, datetime.strftime(now, '%Y/%m/%d %H:%M'))
        return html

    def reply_event(self):
        msg = self.orign_msg
        print('msg:%s' % msg)
        # print('msg_key:%s' % msg.key)
        print('msg_scan_result:%s' % msg.scan_result)
        if msg.key == 'so_code':
            # TODO: 增加搜索编号的方法
            so_num = msg.scan_result
            print(so_num[:9])
            from sales.models import SalesOrder
            try:
                so = SalesOrder.objects.get(order=so_num[:9])
                print(so)
                massage = ({
                               'title': '%s' % so,
                               'description': self.get_description(so),
                               'url': '%s' % self.request.build_absolute_uri(so.get_absolute_url()),
                               # 'image': '%s' % (image.content.url if image else '')
                           },)
                print(massage)
                # massages.append(massage)
            except Exception as e:
                massage = '没有查找到单号：%s' % so_num[:9]
            content = create_reply(massage, msg)
            # print(content)
        else:
            content = create_reply('该条形码没有信息', msg)
        return content.render()


class WechatAuthView(View):
    CORP_ID = corp_id
    SECRET = 'la8maluNMN_imtic0Jp0ECmE71ca2iQ80n3-a8HFFv4'

    client = WeChatClient(
        CORP_ID,
        SECRET
    )

    def dispatch(self, request, *args, **kwargs):
        code = kwargs.get('code', None)
        # print(request.get_full_path())
        # print(request.META.HTTP_HOST)
        path = request.build_absolute_uri()
        url = self.client.oauth.authorize_url(path)
        print(url)
        if code:
            try:
                user_info = self.client.oauth.get_user_info(code)
            except Exception as e:
                print(e)
                # 这里需要处理请求里包含的 code 无效的情况
                return HttpResponse(status=403)
            else:
                request.session['user_info'] = user_info
        else:
            print('go_url')
            return redirect(url)
        return super().dispatch(request, *args, **kwargs)


class WxBlockSearchView(WechatBaseView):
    app_name = 'block_search'

    def get_stocks(self, obj):
        html = ''
        for stock in obj.stock.all():
            if html:
                html += '\n'
            html += '%s' % stock
        return html

    def get_title(self, obj):
        html = ''
        for stock in obj.stock.all():
            if html:
                html += '\n'
            html += '%s' % stock.product
        return html

    def get_description(self, obj):
        html = '库存情况:\n%s\n\n' % self.get_stocks(obj)
        html += '\n品种:%s' % obj.category
        html += '\n矿山:%s' % obj.quarry
        html += '\n批次: %s' % obj.batch
        html += '\n重量:%st' % obj.weight
        html += '\nm3:%s' % obj.get_m3()
        html += '\n尺寸:%s' % obj.get_size()
        html += "\n入库日期:%s" % (datetime.strftime(obj.created, "%Y/%m/%d"))
        return html

    def reply_text(self):
        msg = self.orign_msg
        text = msg.content
        content = create_reply('', msg)
        if text:
            massages = []
            from product.models import Block
            blocks = Block.objects.filter(name__istartswith=text)
            if blocks:
                image = None
                for block in blocks:
                    for file in block.files.all():
                        if file.type == 'image':
                            image = file
                            break
                    # print(block)
                    massage = {
                        'title': '%s' % block,
                        'description': self.get_description(block),
                        'url': '%s' % self.request.build_absolute_uri(block.get_absolute_url()),
                        'image': '%s' % (image.content.url if image else '')
                    }
                    massages.append(massage)
            else:
                massages = '没有查找到编号：%s' % text
            content = create_reply(massages, msg)
            # print(content)
        return content.render()


class WxPaymentView(WechatBaseView):
    app_name = 'payment'
