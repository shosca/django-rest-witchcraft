# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from itertools import chain

import six
from rest_framework import mixins

from sqlalchemy import orm
from sqlalchemy.orm import class_mapper

from django.db.models.constants import LOOKUP_SEP


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


class ExpandableQuerySerializerMixin(QuerySerializerMixin):
    def get_queryset(self):
        queryset = super(ExpandableQuerySerializerMixin, self).get_queryset()

        serializer = self.get_query_serializer()
        serializer.is_valid()

        return self.expand_queryset(queryset, chain(*serializer.validated_data.values()))

    def expand_queryset(self, queryset, values):
        to_expand = []

        for value in values:
            to_load = []
            components = value.split(LOOKUP_SEP)

            model = queryset._entities[0].mapper.class_
            for c in components:
                props = {i.key: i for i in class_mapper(model).iterate_properties}
                try:
                    _field = getattr(model, c)
                    field = props[c]
                    model = field._dependency_processor.mapper.class_
                except (KeyError, AttributeError):
                    to_load = []
                    break
                else:
                    to_load.append(_field)

            if to_load:
                to_expand.append(to_load)

        if to_expand:
            queryset = queryset.options(
                *[six.moves.reduce(lambda a, b: a.joinedload(b), expand, orm) for expand in to_expand]
            )

        return queryset
