# coding=utf-8
"""
@version: 2018/2/26 026
@author: Suen
@contact: zhenghua@pokerlegendpoker.cn
@file: views
@time: 10:40
@note:  ??
"""

from django.http.response import JsonResponse


def hello(request):
    return JsonResponse(data={'hello': 'world'})
