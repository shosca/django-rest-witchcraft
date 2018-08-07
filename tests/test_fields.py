# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from enum import Enum

from rest_framework.exceptions import ValidationError
from rest_framework.fields import ChoiceField
from rest_witchcraft.fields import EnumField, HyperlinkedIdentityField, ImplicitExpandableListField

from django.test import SimpleTestCase

from .models import Owner


class SomeEnum(Enum):
    test1 = 1
    test2 = 2


class TestEnumField(SimpleTestCase):
    def test_choices(self):

        field = EnumField(enum_class=SomeEnum)

        self.assertEqual(field.choices, {1: 1, 2: 2})

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


class TestHyperlinkedIdentityField(SimpleTestCase):
    def test_url_not_saved(self):
        field = HyperlinkedIdentityField(view_name="foo")

        self.assertIsNone(field.get_url(Owner(first_name="Jon", last_name="Snow"), None, None, None))


class TestImplicitExpandableListField(SimpleTestCase):
    def test_to_internal_value(self):
        f = ImplicitExpandableListField(child=ChoiceField(choices=["foo", "foo__bar", "bar"]))

        self.assertEqual(f.run_validation(["foo"]), ["foo"])
        self.assertEqual(set(f.run_validation(["foo__bar"])), {"foo__bar", "foo"})
