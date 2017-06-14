# -*- coding: utf-8 -*-
import datetime
import decimal

from rest_framework import fields
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import sqltypes

from .fields import CharMappingField, EnumField


def get_detail_view_name(model):
    """
    Given a model class, return the view name to use for URL relationships
    that rever to instances of the model.
    """
    return '{}s-detail'.format(model.__name__.lower())


def get_url_kwargs(model):
    field_kwargs = {'read_only': True}

    return field_kwargs


serializer_field_mapping = {
    # sqlalchemy types
    postgresql.HSTORE: CharMappingField,

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

try:
    from sqlalchemy_utils import types

    serializer_field_mapping[types.IPAddressType] = fields.IPAddressField
    serializer_field_mapping[types.UUIDType] = fields.UUIDField
    serializer_field_mapping[types.URLType] = fields.URLField
except ImportError:  # pragma: no cover
    pass


def get_field_type(column):
    """
    Returns the field type to be used determined by the sqlalchemy column type or the column type's python type
    """
    if isinstance(column.type, sqltypes.Enum):
        if column.type.enum_class:
            return EnumField

        return fields.ChoiceField

    if isinstance(column.type, postgresql.ARRAY):
        child_field = serializer_field_mapping.get(column.type.item_type.__class__
                                                   ) or serializer_field_mapping.get(column.type.item_type.python_type)

        if child_field is None:
            raise KeyError("Could not figure out field for ARRAY item type '{}'".format(column.type.__class__))

        class ArrayField(fields.ListField):

            def __init__(self, *args, **kwargs):
                kwargs['child'] = child_field()
                super(ArrayField, self).__init__(*args, **kwargs)

        return ArrayField

    if column.type.__class__ in serializer_field_mapping:
        return serializer_field_mapping.get(column.type.__class__)

    if issubclass(column.type.python_type, bool):
        return fields.NullBooleanField if column.nullable else fields.BooleanField

    return serializer_field_mapping.get(column.type.python_type)
