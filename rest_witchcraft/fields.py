# -*- coding: utf-8 -*-
"""
Some SQLAlchemy specific field types.
"""
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import six
from rest_framework import fields, relations

from django.db.models.constants import LOOKUP_SEP

from django_sorcery.db.meta import model_info


class HyperlinkedIdentityField(relations.HyperlinkedIdentityField):
    def get_url(self, obj, view_name, request, format):
        info = model_info(obj.__class__)

        # Unsaved objects will not yet have a valid URL.
        if not all(getattr(obj, i) for i in info.primary_keys):
            return None

        if len(info.primary_keys) == 1:
            kwargs = {self.lookup_url_kwarg: getattr(obj, self.lookup_field)}
        else:
            kwargs = {k: getattr(obj, k) for k in info.primary_keys}

        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)


class UriField(HyperlinkedIdentityField):
    """
    Represents a uri to the resource
    """

    def get_url(self, obj, view_name, request, format):
        """
        Same as basic HyperlinkedIdentityField except return uri vs full url.
        """
        return super(UriField, self).get_url(obj, view_name, None, format)


class EnumField(fields.ChoiceField):
    """
    Used for SQLAlchemy's Enum column type used in either mapping python Enum's, or
    a list of valid fields for the column.
    """

    def __init__(self, **kwargs):
        self.enum_class = kwargs.pop("enum_class")
        kwargs["choices"] = [(e.value, e.value) for e in self.enum_class]
        kwargs.pop("max_length", None)
        super(EnumField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            return self.enum_class(data)

        except (KeyError, ValueError):
            self.fail("invalid_choice", input=data)

    def to_representation(self, value):
        if not value:
            return None

        return value.value


class CharMappingField(fields.DictField):
    """
    Used for Postgresql HSTORE columns for storing key-value pairs.
    """

    child = fields.CharField(allow_null=True)


class ImplicitExpandableListField(fields.ListField):
    """
    List field which implicitly expands parent field when child field
    is expanded assuming parent field is also expandable by being one of the choices.
    """

    def to_internal_value(self, data):
        data = super(ImplicitExpandableListField, self).to_internal_value(data)
        for i in data[:]:
            parts = i.split(LOOKUP_SEP)
            data = list(
                (set(LOOKUP_SEP.join(parts[:i]) for i in six.moves.range(1, len(parts))) & set(self.child.choices))
                | set(data)
            )
        return data
