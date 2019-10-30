# -*- coding: utf-8 -*-
"""
Some SQLAlchemy specific field types.
"""
# -*- coding: utf-8 -*-

import six

from django.db.models.constants import LOOKUP_SEP

from django_sorcery.db import meta

from rest_framework import fields, relations


class HyperlinkedIdentityField(relations.HyperlinkedIdentityField):
    def get_url(self, obj, view_name, request, format):
        info = meta.model_info(obj.__class__)

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
        return super().get_url(obj, view_name, None, format)


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
        data = super().to_internal_value(data)
        for i in data[:]:
            parts = i.split(LOOKUP_SEP)
            data = list(
                ({LOOKUP_SEP.join(parts[:i]) for i in six.moves.range(1, len(parts))} & set(self.child.choices))
                | set(data)
            )
        return data


class SkippableField(fields.Field):
    """
    Field which is always skipped on to_representation

    Useful when used together with ``ExpandableModelSerializer`` since it allows
    to completely skip expandable field when it is not being expanded.
    Especially useful for ``OneToMany`` relations since by default nested
    serializer cannot be rendered as none of the PKs of the "many" items are
    known unlike ``ManyToOne`` when nested serializer can be rendered with PK.
    For example:

    .. code::

        class FooSerializer(ExpandableModelSerializer):
            bar = BarSerializer(many=True)

            class Meta:
                model = Foo
                session = session
                fields = "__all__"
                expandable_fields = {
                    "bar": SkippableField()
                }
    """

    def get_attribute(self, instance):
        raise fields.SkipField
