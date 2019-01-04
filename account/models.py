from django.db import models
from django.conf import settings


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField('头像', blank=True, null=True, upload_to='user/avatar/%Y%m/', default='logo/logo.jpg')

    class Meta:
        verbose_name = '用户资料'

    def __str__(self):
        return self.user.name