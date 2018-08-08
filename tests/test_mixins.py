# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import six
from rest_framework.fields import IntegerField
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.test import APIRequestFactory
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_witchcraft.mixins import ExpandableQuerySerializerMixin
from rest_witchcraft.serializers import ExpandableModelSerializer, ModelSerializer

from sqlalchemy.orm import joinedload

from django.test import SimpleTestCase

from .models import Vehicle, session
from .test_routers import UnAuthMixin


class DummySerializer(ModelSerializer):
    class Meta(object):
        session = session
        model = Vehicle
        fields = "__all__"


class VehicleOwnerStubSerializer(Serializer):
    id = IntegerField(source="_owner_id")


class VehicleSerializer(ExpandableModelSerializer):
    foo = IntegerField()

    class Meta(object):
        session = session
        model = Vehicle
        expandable_fields = {"owner": VehicleOwnerStubSerializer(source="*", read_only=True), "foo": IntegerField()}
        fields = "__all__"


class DummyViewSet(ExpandableQuerySerializerMixin, GenericViewSet):
    serializer_class = DummySerializer

    def list(self, request, *args, **kwargs):
        return Response()


class ExpandableViewSet(UnAuthMixin, ExpandableQuerySerializerMixin, ModelViewSet):
    serializer_class = VehicleSerializer
    queryset = Vehicle.objects

    def list(self, request, *args, **kwargs):
        r = super(ExpandableViewSet, self).list(request, *args, **kwargs)
        r.data = {"query": six.text_type(self.get_queryset()), "results": r.data}
        return r


class TestDummyViewSet(SimpleTestCase):
    def test_no_queryset(self):
        self.assertIsNone(DummyViewSet().get_query_serializer())


class TestQuerySerializerMixin(SimpleTestCase):
    def setUp(self):
        super(TestQuerySerializerMixin, self).setUp()
        self.rf = APIRequestFactory()

    def test_invalid_query(self):
        view = ExpandableViewSet.as_view(actions={"get": "list"})

        self.assertEqual(view(self.rf.get("/")).status_code, 200)
        self.assertEqual(view(self.rf.get("/", {"expand": "owner"})).status_code, 200)
        self.assertEqual(view(self.rf.get("/", {"expand": "foo"})).status_code, 200)
        self.assertEqual(view(self.rf.get("/", {"expand": "haha"})).status_code, 400)

    def test_no_query_serializer(self):
        view = ExpandableViewSet.as_view(actions={"get": "list"}, serializer_class=DummySerializer)

        self.assertEqual(view(self.rf.get("/")).status_code, 200)

    def test_eagerload_sql(self):
        view = ExpandableViewSet.as_view(actions={"get": "list"})

        self.assertNotIn("LEFT OUTER JOIN", view(self.rf.get("/")).data["query"])
        self.assertNotIn("LEFT OUTER JOIN", view(self.rf.get("/", {"expand": "foo"})).data["query"])

        r = view(self.rf.get("/", {"expand": "owner"}))
        self.assertIn("LEFT OUTER JOIN", r.data["query"])
        self.assertEqual(r.data["query"].count("LEFT OUTER JOIN"), 1)

    def test_already_eagerload(self):
        view = ExpandableViewSet.as_view(
            actions={"get": "list"}, queryset=Vehicle.objects.options(joinedload(Vehicle.owner))
        )

        r = view(self.rf.get("/", {"expand": "owner"}))
        self.assertIn("LEFT OUTER JOIN", r.data["query"])
        # even if we add more joinedloads sqlalchemy should normalize them
        # as that exact path is already joined in base queryset
        self.assertEqual(r.data["query"].count("LEFT OUTER JOIN"), 1)
