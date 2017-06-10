# -*- coding: utf-8 -*-
from rest_framework import fields


class UriField(fields.CharField):

    def __init__(self, *args, **kwargs):
        super(UriField, self).__init__(*args, **kwargs)


class EnumField(fields.ChoiceField):

    def __init__(self, **kwargs):
        self.enum_class = kwargs.pop('enum_class')
        kwargs['choices'] = [(e.name, e.name) for e in self.enum_class]
        kwargs.pop('max_length', None)
        super(EnumField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            return self.enum_class[data]
        except KeyError:
            self.fail('invalid_choice', input=data)

    def to_representation(self, value):
        if not value:
            return None

        return value.name


class CharMappingField(fields.DictField):
    child = fields.CharField(allow_null=True)
