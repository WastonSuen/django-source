# coding=utf-8
"""
@version: 2018/2/26 026
@author: Suen
@contact: zhenghua@pokerlegendpoker.cn
@file: urls
@time: 10:55
@note:  ??
"""

from django.urls import path
import app.test.views

urlpatterns = [
    path('hello', app.test.views.hello, name='hello')
]
