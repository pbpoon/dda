from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.postgres.fields import JSONField


#
#
class Comment(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='用户')
    created = models.DateTimeField('创建时间', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    content = models.TextField('内容')
    # text = models.TextField('内容')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = '评论信息'
        ordering = ('-created',)


class OperationLogs(models.Model):
    """操作日志"""
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    from_order = GenericForeignKey('content_type', 'object_id')
    pre_data = JSONField('前数据')
    content = models.TextField(verbose_name="修改详情", null=True)

    class Meta:
        verbose_name = '操作日志'


#


def compare(oldstr, newstr, field, msg):
    """
    生成操作日志详细记录
    :param oldstr: 原值
    :param newstr: 新值
    :param field: 目标字段
    :return: content
    """
    content = ''

    if isinstance(newstr, list):  # 将list转为str类型，list对象存储到数据库后，为str类型
        newstr = str(newstr)

    if oldstr == newstr:  # 值未变化，不做处理
        pass
    else:
        if not msg:
            content = ('"%s"由"%s"变为"%s";' % (field, oldstr, newstr))
        else:
            content = ('%s"%s"由"%s"变为"%s";' % (msg, field, oldstr, newstr))
    return content


def getmodelfield(modelname):
    """获取model 指定字段的 verbose_name属性值"""
    fielddic = {}
    for field in modelname._meta.fields:
        fielddic[field.name] = field.verbose_name
    return (fielddic)


def operationlogs(object_old_model, dict_update_fields, type, msg=None):
    """
    操作日志
    :param object_old_model: 旧的model对象实例
    :param dict_update_fields: 更新的字段键值对--字典格式
    :param type: 类型 (自己定义)
    :param msg: 自定义日志内容 (如果日志格式非‘A由aa变为bb’，可使用此参数)
    :return:
    """
    content = ''

    if object_old_model is not None and dict_update_fields is not None:
        fielddic = getmodelfield(object_old_model)
        for key, val in dict_update_fields.items():
            if isinstance(val, dict):  # 获取外键表的字段值
                _model = getattr(object_old_model, key)
                for _key, _val in val.items():  # key->外键名
                    if _key == "id":  # 主键id不参与对比
                        pass
                    else:
                        if not _model:  # 如果原值为null，做单独处理
                            _rtn = '"%s"由""变为"%s";' % (fielddic[key], _val)
                        else:  # 如果原值不为null，调用对比函数处理
                            _rtn = compare(getattr(_model, _key), _val, fielddic[key], msg)
                        content = content + _rtn
            else:
                _rtn = compare(getattr(object_old_model, key), val, fielddic[key], msg)
                content = content + _rtn
    else:
        content = msg

    #  存储日志
    if content == '':
        pass
    else:
        obj_operationlogs = OperationLogs()
        obj_operationlogs.content = content
        obj_operationlogs.type = type
        obj_operationlogs.save()
