# -*- coding: utf-8 -*-
from django.conf.urls import url


urlpatterns = [url(r"^example/(?P<id>.+)/$", lambda: None, name="owner")]
