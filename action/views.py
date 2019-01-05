# from django.http import HttpResponse
# from django.shortcuts import render
#
# # Create your views here.
# from django.views.generic.base import View
# from wechatpy import parse_message, create_reply
# from wechatpy.enterprise.client import WeChatClient
# from wechatpy.enterprise.crypto import WeChatCrypto
# from wechatpy.exceptions import InvalidSignatureException
# from wechatpy.replies import BaseReply
#
# corp_id = 'wwb132fd0d32417e5d'
# secret = 'la8maluNMN_imtic0Jp0ECmE71ca2iQ80n3'
# token = 'sdfwf'
#
#
# class WechatView(View):
#     # client = WeChatCrypto(token, corp_id, secret)
#
#     def get(self, request, *args, **kwargs):
#         signature = request.GET.get('signature', '')
#         timestamp = request.GET.get('timestamp', '')
#         nonce = request.GET.get('nonce', '')
#         echo_str = request.GET.get('echostr', '')
#         try:
#             self.client.check_signature(signature, timestamp, nonce)
#         except InvalidSignatureException:
#             echo_str = 'error'
#         response = HttpResponse(echo_str, content_type="text/plain")
#         return response
#
#     # POST方式用于接受和返回请求
#     def post(self, request, *args, **kwargs):
#         reply = None
#         msg = parse_message(request.body)
#         # 判断消息类型，文本消息则调用reply_text进行处理
#         if msg.type == 'text':
#             reply = self.reply_text.do_reply(msg)
#         elif msg.type == 'event':
#             reply = self.reply_event.do_reply(msg)
#         else:
#             pass
#         if not reply or not isinstance(reply, BaseReply):
#             reply = create_reply('暂不支持您所发送的消息类型哟~ 回复“帮助”查看使用说明。', msg)
#         response = HttpResponse(reply.render(), content_type="application/xml")
#         return response
#
#     def do_reply(self, msg):
#         reply = None
#         try:
#             if msg.content == '天气':
#                 # msg.content即为消息内容
#                 reply = create_reply('相关回复文本', msg)
#             else:
#                 reply = create_reply('没有此关键词', msg)
#         except Exception as e:
#             print('error:', e)
#         return reply
