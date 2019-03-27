from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ObjectDoesNotExist
from wechatpy.enterprise import WeChatClient
from django.conf import settings


class Action(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, db_index=True, related_name='action',
                             verbose_name='用户')
    verb = models.CharField('动作', max_length=255)
    target_ct = models.ForeignKey(ContentType, blank=True, null=True, related_name='target_obj',
                                  on_delete=models.CASCADE)
    target_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    target = GenericForeignKey('target_ct', 'target_id')
    created = models.DateTimeField('发生时间', auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('created',)


class WxConfig(models.Model):
    name = models.CharField('应用名称', max_length=20)
    app_name = models.CharField(max_length=80)
    corp_id = models.CharField(max_length=80)
    agent_id = models.CharField(max_length=80)
    values = JSONField()

    class Meta:
        verbose_name = '微信企业设置'

    def __str__(self):
        return self.name


class WxConf:
    def __init__(self, app_name, corp_id=None, agent_id=None):
        self.app_name = app_name
        self.value = self.get_value()

    def get_value(self):
        try:
            print(self.app_name + '11111')
            values = WxConfig.objects.get(app_name=self.app_name).values
            print(values)
            return values
        except ObjectDoesNotExist:
            return {}

    def __getattr__(self, item):
        return self.value.get(item, None)


class SchemeWxPush(models.Model):
    time = models.DateTimeField('时间')
    title = models.CharField('标题', max_length=80)
    description = models.CharField('内容', max_length=200, blank=True, null=True)
    url = models.URLField('链接', blank=True, null=True)
    app_name = models.CharField('推送app', max_length=200)
    user_ids = models.TextField('推送用户', default='@all')

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = '计划微信推送'

    def __str__(self):
        return '%s@%s' % (self.title, self.time)

    def get_obj(self):
        return self.content_type.model_class().objects.get(pk=self.object_id)

    def get_url(self):
        if self.url:
            return self.url
        print('url:', settings.DEFAULT_DOMAIN)
        print('abs:', self.get_obj().get_absolute_url())

        return "%s%s" % (settings.DEFAULT_DOMAIN, self.get_obj().get_absolute_url())

    def get_title(self):
        if not self.title:
            return "[%s]%s" % (self.get_obj()._meta.verbose_name, self.title)
        return self.title

    def get_description(self):
        if self.description:
            return self.description
        html = '%s' % self.time
        return html

    def sent_msg(self):
        if not self.app_name:
            return False
        try:
            wx_conf = WxConf(app_name=self.app_name)
            client = WeChatClient(wx_conf.corp_id, wx_conf.Secret)
            print(client, 'client\n')
            print(self.get_title(), 'title')
            print('agent_id:', wx_conf.AgentId)
            print('url:', self.get_url())
            print('desc:', self.get_description())
            client.message.send_text_card(agent_id=wx_conf.AgentId, user_ids=self.user_ids, title=self.get_title(),
                                          description=self.get_description(),
                                          url=self.get_url())
            print('out')
        except Exception as e:
            print(e)
        return True
