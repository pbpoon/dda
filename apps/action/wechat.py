#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/1/6
from wechatpy.enterprise import WeChatClient
import uuid
import time
from django.conf import settings


class WxClient:
    app_name = None
    user_ids = '@all'
    wx_conf = None

    def get_wx_conf(self):
        from action.models import WxConf
        return WxConf(app_name=self.app_name)

    def get_client(self):
        if not self.app_name:
            return False
        try:
            self.wx_conf = self.get_wx_conf()
            # print(wx_conf,'in')
            return WeChatClient(self.wx_conf.corp_id, self.wx_conf.Secret)
        except Exception as e:
            print(e)
            raise ValueError('获取企业微信资料错误')


class WxJsSdkMixin(WxClient):

    def get_js_sdk_url(self):
        if self.object:
            if hasattr(self, 'get_url'):
                return self.get_url()
            raise ValueError('define get_jssdk_url method')
        return ''

    def get_js_sdk_data(self):
        self.client = self.get_client()
        url = self.get_js_sdk_url()
        noncestr = str(uuid.uuid1())[:12]
        ticket = self.client.jsapi.get_jsapi_ticket()
        timestamp = int(time.time())
        signature = self.client.jsapi.get_jsapi_signature(noncestr, ticket, timestamp, url)
        return {
            'signature': signature,
            'noncestr': noncestr,
            'timestamp': timestamp,
            'appid': self.wx_conf.corp_id,
            'url': url,
        }

    def get_js_sdk_desc(self):
        # raise ValueError('define get_js_sdk_desc method')
        return ''

    def get_js_sdk_title(self):
        if self.object:
            return f'{self.object._meta.verbose_name}/{self.object}'
        return ""

    def get_js_sdk_link(self):
        if self.object:
            return self.object.get_absolute_url()
        return ""

    def get_js_sdk_img_url(self):
        return '/static/image/logo.jpg'

    def get_js_sdk_display(self):
        data = {
            'title': self.get_js_sdk_title(),
            'desc': self.get_js_sdk_desc(),
            'link': self.get_js_sdk_link(),
            'img_url': f'{settings.DEFAULT_DOMAIN}{self.get_js_sdk_img_url()}'
        }
        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jsdata'] = self.get_js_sdk_data()
        context['jsdisplay'] = self.get_js_sdk_display()
        return context


class SentWxMsgMixin(WxJsSdkMixin):

    def get_url(self):
        return "%s" % (self.request.build_absolute_uri(self.object.get_absolute_url()))

    def get_title(self):
        raise ValueError('define get_title')

    def get_description(self):
        raise ValueError('define get_description')

    def sent_msg(self):
        # print(client, '222')
        self.client = self.get_client()
        print(self.get_title(), 'title')
        self.client.message.send_text_card(agent_id=self.wx_conf.AgentId, user_ids=self.user_ids,
                                           title=self.get_title(),
                                           description=self.get_description(),
                                           url=self.get_url())
