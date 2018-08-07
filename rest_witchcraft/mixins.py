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

    Query will be validated as part of query viewset initialization
    therefore query will be validated before any of the viewset actions
    are executed.

    In addition query serializer will be included in serializer context
    for standard viewset serializers. That
    """

    query_serializer_class = None

    @property
    def query_serializer(self):
        return getattr(self, "_query_serializer", None)

    @query_serializer.setter
    def query_serializer(self, value):
        self._query_serializer = value

    def get_query_serializer_class(self):
        return (
            self.query_serializer_class
            or getattr(self.get_serializer_class()(), "get_query_serializer_class", lambda: None)()
        )

    def get_query_serializer_context(self):
        return self.get_serializer_context()

    def get_query_serializer(self, *args, **kwargs):
        serializer_class = kwargs.pop("serializer_class", None) or self.get_query_serializer_class()
        if serializer_class is None:
            return
        kwargs.setdefault("context", self.get_query_serializer_context())
        kwargs.setdefault("data", dict(self.request.GET.lists()))
        self.query_serializer = serializer = serializer_class(*args, **kwargs)
        serializer.is_valid()
        return serializer

    def check_query(self):
        serializer = self.get_query_serializer()
        if serializer is not None:
            serializer.is_valid(raise_exception=True)

    def initial(self, request, *args, **kwargs):
        super(QuerySerializerMixin, self).initial(request, *args, **kwargs)
        self.check_query()


class ExpandableQuerySerializerMixin(QuerySerializerMixin):
    """
    Adds expandable query serializer validation logic to viewset
    as well as automatic eager load of expanded fields on the serializer.

    The query serializer is expected to be generated by
    :py:meth:`rest_witchcraft.serializers.ExpandableModelSerializer.query_serializer`.
    """

    def get_queryset(self):
        queryset = super(ExpandableQuerySerializerMixin, self).get_queryset()

        serializer = self.query_serializer
        if serializer is None:
            return queryset

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

    def get_serializer_context(self):
        context = super(ExpandableQuerySerializerMixin, self).get_serializer_context()
        context["query_serializer"] = self.query_serializer
        return context
