# -*- coding: utf-8 -*-
from rest_framework import routers


class DefaultRouter(routers.DefaultRouter):

    def get_default_base_name(self, viewset):

        serializer_class = getattr(viewset, 'serializer_class', None)

        if serializer_class:
            return serializer_class.Meta.model.__name__.lower()

        return super(DefaultRouter, self).get_default_base_name(viewset)

    def get_lookup_regex(self, viewset, lookup_prefix=''):

        lookup_url_regex = getattr(viewset, 'lookup_url_regex', None)
        if lookup_url_regex:
            return lookup_url_regex

        return super(DefaultRouter, self).get_lookup_regex(viewset, lookup_prefix)
