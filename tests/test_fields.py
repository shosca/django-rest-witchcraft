# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from enum import Enum

from rest_framework.exceptions import ValidationError
from rest_witchcraft.fields import EnumField

from django.test import SimpleTestCase


class SomeEnum(Enum):
    test1 = 1
    test2 = 2


class TestEnumField(SimpleTestCase):

    def test_to_internal_value_works(self):

        field = EnumField(enum_class=SomeEnum)

        value = field.to_internal_value(2)

        self.assertEqual(value, SomeEnum.test2)

    def test_to_internal_value_validates(self):

        field = EnumField(enum_class=SomeEnum)

        with self.assertRaises(ValidationError):
            field.to_internal_value("test3")

    def test_to_representation_works(self):

        field = EnumField(enum_class=SomeEnum)

        value = field.to_representation(SomeEnum.test1)

        self.assertEqual(value, 1)

    def test_to_representation_handles_none(self):

        field = EnumField(enum_class=SomeEnum)

        value = field.to_representation(None)

        self.assertIsNone(value)
