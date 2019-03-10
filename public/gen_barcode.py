#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/2/28
import base64
import barcode
from barcode.writer import ImageWriter
from io import BytesIO


class GenBarcode:
    def __init__(self, text_value, barcode_type='ean13', writer=ImageWriter()):
        f = BytesIO()
        self.ean = barcode.get(barcode_type, text_value, writer=writer)
        self.ean.write(f)
        # image = self.ean.save()
        image = base64.b64encode(f.getvalue())
        self.value = image.decode('utf8')


if __name__ == '__main__':
    GenBarcode('12355521')
