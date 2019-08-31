# -*- coding: utf-8 -*-
"""
Field mapping from SQLAlchemy type's to DRF fields
"""
# -*- coding: utf-8 -*-
import datetime
import decimal

import six

from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import sqltypes

from django_sorcery.db import meta

from rest_framework import fields

from rest_enumfield import EnumField

from .fields import CharMappingField


def get_detail_view_name(model):
    """
    Given a model class, return the view name to use for URL relationships
    that rever to instances of the model.
    """
    # TODO split camel case
    return "{}-detail".format(model.__name__.lower())


def get_url_kwargs(model):
    """
    Gets kwargs for the UriField
    """
    info = meta.model_info(model)
    lookup_field = list(info.primary_keys.keys())[0]

    field_kwargs = {
        "read_only": True,
        "view_name": get_detail_view_name(model),
        "lookup_field": lookup_field,
        "lookup_url_kwarg": "pk",
    }

    return field_kwargs


SERIALIZER_FIELD_MAPPING = {
    # sqlalchemy types
    postgresql.HSTORE: CharMappingField,
    sqltypes.Enum: EnumField,
    # python types
    datetime.date: fields.DateField,
    datetime.datetime: fields.DateTimeField,
    datetime.time: fields.TimeField,
    datetime.timedelta: fields.DurationField,
    decimal.Decimal: fields.DecimalField,
    float: fields.FloatField,
    int: fields.IntegerField,
    str: fields.CharField,
}
SERIALIZER_FIELD_MAPPING[six.text_type] = fields.CharField
for stype in six.string_types:
    SERIALIZER_FIELD_MAPPING[stype] = fields.CharField

try:
    from sqlalchemy_utils import types

    SERIALIZER_FIELD_MAPPING[types.IPAddressType] = fields.IPAddressField
    SERIALIZER_FIELD_MAPPING[types.UUIDType] = fields.UUIDField
    SERIALIZER_FIELD_MAPPING[types.URLType] = fields.URLField
except ImportError:  # pragma: no cover
    pass


def get_field_type(column):
    """
    Returns the field type to be used determined by the sqlalchemy column type or the column type's python type
    """
    if isinstance(column.type, sqltypes.Enum) and not column.type.enum_class:
        return fields.ChoiceField

    if isinstance(column.type, postgresql.ARRAY):
        child_field = SERIALIZER_FIELD_MAPPING.get(column.type.item_type.__class__) or SERIALIZER_FIELD_MAPPING.get(
            column.type.item_type.python_type
        )

        if child_field is None:
            raise KeyError("Could not figure out field for ARRAY item type '{}'".format(column.type.__class__))

        class ArrayField(fields.ListField):
            """Nested array field for PostreSQL's ARRAY type"""

            def __init__(self, *args, **kwargs):
                kwargs["child"] = child_field()
                super().__init__(*args, **kwargs)

        return ArrayField

    if column.type.__class__ in SERIALIZER_FIELD_MAPPING:
        return SERIALIZER_FIELD_MAPPING.get(column.type.__class__)

    if issubclass(column.type.python_type, bool):
        return fields.NullBooleanField if column.nullable else fields.BooleanField

    for typ in column.type.python_type.mro():
        if typ in SERIALIZER_FIELD_MAPPING:
            return SERIALIZER_FIELD_MAPPING.get(typ)
