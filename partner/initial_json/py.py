#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/10
import json


def make_format(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


json = make_format('province.json')

print(json)