#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/2
from .models import Comment


def create_comment(user, comment):
    cm = Comment(user=user, comment=comment)
    cm.save()
