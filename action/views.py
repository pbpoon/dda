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
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.enterprise.client import WeChatClient
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.replies import BaseReply, create_reply

from action.models import WxConf

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

    def dispatch(self, request, *args, **kwargs):
        wx_conf = self.get_wx_conf()
        self.crypto = WeChatCrypto(wx_conf.Token, wx_conf.EncodingAESKey, wx_conf.corp_id)

        self.wx_data['signature'] = request.GET.get('msg_signature', '')
        self.wx_data['timestamp'] = request.GET.get('timestamp', '')
        self.wx_data['nonce'] = request.GET.get('nonce', '')
        echo_str = request.GET.get('echostr', '')
        try:
            echo_str = self.crypto.check_signature(
                echo_str=echo_str, **self.wx_data
            )
            return super().dispatch(request, echo_str, *args, **kwargs)
        except InvalidSignatureException:
            echo_str = 'error'
        return HttpResponse(echo_str)

    def get(self, request, echo_str, *args, **kwargs):
        return HttpResponse(echo_str)

    #     # POST方式用于接受和返回请求
    def post(self, request, *args, **kwargs):
        reply = None
        msg = self.crypto.decrypt_message(request.body, **self.wx_data)
        # 判断消息类型，文本消息则调用reply_text进行处理
        if msg.type == 'text':
            reply = self.reply_text.do_reply(msg)
        elif msg.type == 'event':
            reply = self.reply_event.do_reply(msg)
        else:
            pass
        if not reply or not isinstance(reply, BaseReply):
            reply = create_reply('暂不支持您所发送的消息类型哟~ 回复“帮助”查看使用说明。', msg)
        response = HttpResponse(reply.render(), content_type="application/xml")
        return response


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
