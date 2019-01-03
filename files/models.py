import os
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.template.loader import render_to_string

FILES_TYPE = (
    ('image', '图片'), ('video', '视频'), ('pdf', 'PDF'), ('doc', 'word文档'), ('xls', 'Excel文档')
)


def get_upload_to(instance, filename):
    # _, extension = filename.split('.')
    obj = instance.get_obj()
    app_name, model_name = obj._meta.label_lower.split('.')
    return '%s/%s/%s/%s' % (app_name, model_name, instance.get_obj_str(), filename)


class Files(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey('content_type', 'object_id')
    content = models.FileField(upload_to=get_upload_to)
    desc = models.CharField('简述', max_length=120, blank=True, null=True)
    entry = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='登记人',
                              related_name='%(class)s_entry')

    class Meta:
        verbose_name = '文件'

    def get_obj(self):
        return self.content_type.model_class().objects.get(pk=self.object_id)

    def get_obj_str(self):
        obj = self.get_obj()
        obj_str = str(obj)
        if hasattr(obj, 'order'):
            if isinstance(obj.order, str):
                obj_str = obj.order
        elif hasattr(obj, 'name'):
            obj_str = obj.name
        return obj_str

    @property
    def type(self):
        name, _ = os.path.splitext(self.content.name)
        extension = _.split('.')[1]
        if extension.lower() in ('jpg', 'jpeg', 'png', 'gif', 'bmp'):
            return 'image'
        elif extension.lower() == 'pdf':
            return 'pdf'
        elif extension.lower() in ('doc', 'docx'):
            return 'word'
        elif extension.lower() in ('xls', 'xlsx'):
            return 'excel'
        else:
            return extension.lower()

    def get_type_display(self):
        try:
            name = dict(FILES_TYPE)[self.type]
        except Exception as e:
            name = self.type
        return name

    def get_template_name(self):
        type = self.type
        folder = 'files/'
        if type == 'image':
            name = 'image.html'
        else:
            name = 'file.html'
        return folder + name

    def render(self):
        return render_to_string(self.get_template_name(), {'item': self})

    def create_comment(self):
        if hasattr(self.get_obj(), 'comments'):
            comment = '添加%s:<i>%s</i>%s' % (self.get_type_display(), self.content.name, self.render())
            self.get_obj().comments.create(user=self.entry, content=comment)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.create_comment()
