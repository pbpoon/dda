import os

from PIL import ImageDraw, ImageFont
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.template.loader import render_to_string

from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile

import sys

FILES_TYPE = (
    ('image', '图片'), ('video', '视频'), ('pdf', 'PDF'), ('doc', 'word文档'), ('xls', 'Excel文档')
)


def get_upload_to(instance, filename):
    # _, extension = filename.split('.')
    obj = instance.get_obj()
    app_name, model_name = obj._meta.label_lower.split('.')
    return '%s/%s/%s/%s' % (app_name, model_name, instance.get_obj_str(), filename)


# 指定要使用的字体和大小；/Library/Fonts/是macOS字体目录；Linux的字体目录是/usr/share/fonts/
# try:
#     font = ImageFont.truetype('/Library/Fonts/Arial.ttf', 24)
# except Exception as e:


class Files(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey('content_type', 'object_id')
    content = models.FileField(upload_to=get_upload_to)
    desc = models.CharField('简述', max_length=120, blank=True, null=True)
    entry = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='登记人',
                              related_name='%(class)s_entry')
    created = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '文件'
        ordering = ['-created']

    def __str__(self):
        name = self.content.name.split('/')[-1]
        name = '[%s]%s:%s' % (self.get_type_display(), self.desc if self.desc else '', name)
        return name

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

    # image: 图片   text：要添加的文本  font：字体
    def _add_text_to_image(self, image, text):
        # rgba_image = image.convert('RGBA')
        # text_overlay = Image.new('RGBA', rgba_image.size, (255, 255, 255, 0))
        # bg_w, bg_h = image.size
        # bg_im = Image.new('RGB', image.size)
        image_draw = ImageDraw.Draw(image)
        xSize, ySize = image.size
        fontSize = min(xSize, ySize) // 26
        font = ImageFont.truetype('/usr/share/fonts/FangYuanHeiTiST-2.ttf', fontSize)

        text_size_x, text_size_y = image_draw.textsize(text, font=font)
        # 设置文本文字位置
        # print(rgba_image)
        # x, y = (rgba_image.size[0] - text_size_x), (rgba_image.size[1] - text_size_y)
        # 设置文本颜色和透明度
        outline_color = 'red'
        text_color = 'white'
        outline_move = fontSize * 0.03
        x = 0.03 * xSize
        y = 0.96 * ySize - text_size_y
        image_draw.text((x - outline_move, y - outline_move), text, font=font, fill=outline_color)
        image_draw.text((x + outline_move, y - outline_move), text, font=font, fill=outline_color)
        image_draw.text((x - outline_move, y + outline_move), text, font=font, fill=outline_color)
        image_draw.text((x + outline_move, y + outline_move), text, font=font, fill=outline_color)
        image_draw.text((x, y), text, font=font, fill=text_color)

        # logo
        # logo_x = xSize * 0.8 - fontSize
        # logo_y = xSize * 0.1
        # logo_text = '宏建石材'
        # image_draw.text((logo_x - outline_move, logo_y - outline_move), logo_text, font=font, fill=outline_color)
        # image_draw.text((logo_x + outline_move, logo_y - outline_move), logo_text, font=font, fill=outline_color)
        # image_draw.text((logo_x - outline_move, logo_y + outline_move), logo_text, font=font, fill=outline_color)
        # image_draw.text((logo_x + outline_move, logo_y + outline_move), logo_text, font=font, fill=outline_color)
        # image_draw.text((logo_x, logo_y), logo_text, font=font, fill=text_color)
        del image_draw

        return image

    def save(self, *args, **kwargs):
        if self.type == 'image':
            im = Image.open(self.content)
            sizehold = 1 * 1024 * 1024
            if self.content.size > sizehold:
                width, height = im.size
                p_size = 'long' if width > height else 'tall'
                if p_size == 'long':
                    new_width, new_height = 3072, int(3072 / (width * 1.0 / height))
                else:
                    new_width, new_height = int(3072 / (width * 1.0 / height)), 3072
                im = im.resize((new_width, new_height))
            output = BytesIO()
            obj = self.get_obj()
            company = '宏建石材\n\n'
            if obj._meta.model_name in ('block', 'product'):
                company = '宏建石材 / %s\n\n' % obj.category.name
                size = ''
                for stock in obj.stock.all():
                    if size:
                        size += '\n'
                    if not stock.main_long:
                        continue
                    size += '%s厚' % stock.product.thickness if stock.product.type != 'block' else ''
                    size += '(%s x %s' % (stock.main_long, stock.main_height)
                    if stock.main_width:
                        size += ' x %s)' % stock.main_width
                    else:
                        size += ')  '
                text = company + '编号:%s# 规格:%s' % (obj.name, size)
            else:
                text = company + str(obj)
            result_im = self._add_text_to_image(im, text)
            result_im = result_im.convert('RGB')
            result_im.save(output, 'jpeg')
            output.seek(0)

            # change the imagefield value to be the newley modifed image value
            self.content = InMemoryUploadedFile(output, 'FileField', "%s.jpg" % self.content.name.split('.')[0],
                                                'image/jpeg',
                                                sys.getsizeof(output), None)
        super().save(*args, **kwargs)
        self.create_comment()
