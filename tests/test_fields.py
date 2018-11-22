# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from enum import Enum

from rest_framework.exceptions import ValidationError
from rest_framework.fields import ChoiceField
from rest_witchcraft.fields import EnumField, HyperlinkedIdentityField, ImplicitExpandableListField, UriField

from django.conf.urls import url
from django.test import SimpleTestCase, override_settings

from .models import Owner
from .models_composite import RouterTestCompositeKeyModel


class SomeEnum(Enum):
    test1 = 1
    test2 = 2


class TestEnumField(SimpleTestCase):
    def test_choices(self):

        field = EnumField(enum_class=SomeEnum)

        self.assertDictEqual(field.choices, {"test1": 1, "test2": 2})

        field = EnumField(choices=SomeEnum)

        self.assertDictEqual(field.choices, {"test1": 1, "test2": 2})

    def test_to_internal_value_works(self):

        field = EnumField(enum_class=SomeEnum)

        self.assertEqual(field.to_internal_value(2), SomeEnum.test2)
        self.assertEqual(field.to_internal_value("test2"), SomeEnum.test2)

        field = EnumField(choices=SomeEnum)

        self.assertEqual(field.to_internal_value(2), SomeEnum.test2)
        self.assertEqual(field.to_internal_value("test2"), SomeEnum.test2)

    def test_to_internal_value_validates(self):

        field = EnumField(enum_class=SomeEnum)

        with self.assertRaises(ValidationError):
            field.to_internal_value("test3")

        with self.assertRaises(ValidationError):
            field.to_internal_value(3)

        field = EnumField(choices=SomeEnum)

        with self.assertRaises(ValidationError):
            field.to_internal_value("test3")

        with self.assertRaises(ValidationError):
            field.to_internal_value(3)

    def test_to_representation_works(self):

        field = EnumField(enum_class=SomeEnum)

        self.assertEqual(field.to_representation(SomeEnum.test1), "test1")

    def test_to_representation_handles_none(self):

        field = EnumField(enum_class=SomeEnum)

        value = field.to_representation(None)

        self.assertIsNone(value)


@override_settings(ROOT_URLCONF=[url(r"^example/(?P<id>.+)/$", lambda: None, name="owner")])
class TestHyperlinkedIdentityField(SimpleTestCase):
    def test_url(self):
        field = HyperlinkedIdentityField(view_name="foo", lookup_url_kwarg="id", lookup_field="id")
        owner = Owner(id=1, first_name="Jon", last_name="Snow")

        url = field.get_url(owner, "owner", None, None)
        self.assertEqual(url, "/example/1/")

    def test_url_not_saved(self):
        field = HyperlinkedIdentityField(view_name="foo")

        self.assertIsNone(field.get_url(Owner(first_name="Jon", last_name="Snow"), "owner", None, None))


@override_settings(ROOT_URLCONF=[url(r"^example/(?P<id>.+)/(?P<other_id>.+)/$", lambda: None, name="owner")])
class TestHyperlinkedIdentityFieldComposite(SimpleTestCase):
    def test_url_composite(self):
        field = HyperlinkedIdentityField(view_name="foo")
        instance = RouterTestCompositeKeyModel(id=1, other_id=2)

        url = field.get_url(instance, "owner", None, None)

        self.assertEqual(url, "/example/1/2/")


@override_settings(ROOT_URLCONF=[url(r"^example/(?P<id>.+)/$", lambda: None, name="owner")])
class TestUriField(SimpleTestCase):
    def test_url(self):
        field = UriField(view_name="foo", lookup_url_kwarg="id", lookup_field="id")
        owner = Owner(id=1, first_name="Jon", last_name="Snow")

        url = field.get_url(owner, "owner", None, None)
        self.assertEqual(url, "/example/1/")


class TestImplicitExpandableListField(SimpleTestCase):
    def test_to_internal_value(self):
        f = ImplicitExpandableListField(child=ChoiceField(choices=["foo", "foo__bar", "bar"]))

        self.assertEqual(f.run_validation(["foo"]), ["foo"])
        self.assertEqual(set(f.run_validation(["foo__bar"])), {"foo__bar", "foo"})
