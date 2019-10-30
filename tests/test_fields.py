# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.test import SimpleTestCase, override_settings

from rest_framework.fields import ChoiceField, IntegerField
from rest_framework.serializers import Serializer

from rest_witchcraft.fields import HyperlinkedIdentityField, ImplicitExpandableListField, SkippableField, UriField

from .models import Owner
from .models_composite import RouterTestCompositeKeyModel


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


class TestSkippableField(SimpleTestCase):
    def test_field_always_skippable(self):
        class TestSerializer(Serializer):
            foo = SkippableField()
            bar = IntegerField()

        self.assertEqual(TestSerializer(instance={"foo": "foo", "bar": 5}).data, {"bar": 5})
