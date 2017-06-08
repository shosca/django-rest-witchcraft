# -*- coding: utf-8 -*-
import contextlib
import inspect
from collections import OrderedDict
from itertools import chain

import six
from django.utils.text import capfirst
from sqlalchemy import inspect as sa_inspect

try:
    suppress = contextlib.suppress
except AttributeError:

    @contextlib.contextmanager
    def suppress(*exceptions):
        try:
            yield
        except exceptions:
            pass


if six.PY2:

    def get_args(func):
        return inspect.getargspec(func).args[1:]
else:

    def get_args(func):
        return list(inspect.signature(func).parameters.keys())[1:]


_registry = {}


class composite_info(object):
    __slots__ = ('prop', 'properties', '_field_names')

    def __init__(self, composite):
        self._field_names = set()
        self.prop = composite.prop
        attrs = get_args(self.prop.composite_class.__init__)

        self.properties = {}
        for attr, prop, col in zip(attrs, self.prop.props, self.prop.columns):
            self.properties[attr] = _column_info(prop, col)

    @property
    def field_names(self):
        if not self._field_names:
            self._field_names.update(self.properties.keys())

            self._field_names = [attr for attr in self._field_names if not attr.startswith('_')]

        return self._field_names


class _column_info(object):
    __slots__ = ('property', 'column')

    def __init__(self, property, column):
        self.property = property
        self.column = column

    @property
    def field_kwargs(self):
        kwargs = {}

        kwargs['label'] = capfirst(self.property.key)
        kwargs['help_text'] = self.property.doc

        with suppress(AttributeError):
            enum_class = self.column.type.enum_class
            if enum_class is not None:
                kwargs['enum_class'] = self.column.type.enum_class
            else:
                kwargs['choices'] = self.column.type.enums

        with suppress(AttributeError):
            kwargs['max_digits'] = self.column.type.precision

        with suppress(AttributeError):
            kwargs['decimal_places'] = self.column.type.scale

        with suppress(AttributeError):
            kwargs['max_length'] = self.column.type.length

        kwargs['required'] = not self.column.nullable
        kwargs['allow_null'] = self.column.nullable

        return kwargs


def model_info(model):
    return _registry.setdefault(model, _model_info(model))


class _model_info(object):
    __slots__ = ('mapper', 'properties', '_field_names', 'model_class', 'composites', 'primary_keys', 'relationships')

    def __init__(self, model):
        self.model_class = model
        self.mapper = sa_inspect(model)
        self._field_names = None
        self.properties = {}
        self.composites = {}
        self.relationships = {}
        self.primary_keys = OrderedDict()

        for col in self.mapper.primary_key:
            attr = self.mapper.get_property_by_column(col)
            self.primary_keys[attr.key] = _column_info(attr, col)

        for col in self.mapper.columns:
            attr = self.mapper.get_property_by_column(col)
            if attr.key not in self.primary_keys:
                self.properties[attr.key] = _column_info(attr, col)

        for composite in self.mapper.composites:
            self.composites[composite.key] = composite_info(getattr(model, composite.key))

        for relationship in self.mapper.relationships:
            self.relationships[relationship.key] = relationship

    @property
    def field_names(self):
        if not self._field_names:
            self._field_names = [
                attr
                for attr in chain(
                    self.primary_keys.keys(), self.properties.keys(), self.composites.keys(), self.relationships.keys()
                ) if not attr.startswith('_')
            ]

        return self._field_names


def get_primary_keys(model, kwargs):
    info = model_info(model)
    pks = []

    for attr, property in info.primary_keys.items():
        pk = kwargs.get(attr)
        pks.append(pk)

    return next(iter(pks), None) if len(pks) < 2 else tuple(pks)
