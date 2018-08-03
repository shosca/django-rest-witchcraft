# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from rest_framework import mixins


class DestroyModelMixin(mixins.DestroyModelMixin):
    """
    Deletes a model instance
    """

    def perform_destroy(self, instance):
        session = self.get_session()
        session.delete(instance)


class QuerySerializerMixin(object):
    """
    Adds query serializer validation logic to viewset
    """

    query_serializer_class = None

    def get_query_serializer_class(self):
        serializer_class = (
            self.query_serializer_class or getattr(self.get_serializer_class(), "query_serializer", lambda: None)()
        )
        return serializer_class

    def get_query_serializer_context(self):
        return self.get_serializer_context()

    def get_query_serializer(self, *args, **kwargs):
        serializer_class = kwargs.pop("serializer_class", None) or self.get_query_serializer_class()
        if serializer_class is None:
            return
        kwargs.setdefault("context", self.get_query_serializer_context())
        kwargs.setdefault("data", dict(self.request.GET.lists()))
        return serializer_class(*args, **kwargs)

    def check_query(self):
        serializer = self.get_query_serializer()
        if serializer is not None:
            serializer.is_valid(raise_exception=True)

    def initial(self, request, *args, **kwargs):
        super(QuerySerializerMixin, self).initial(request, *args, **kwargs)
        self.check_query()
