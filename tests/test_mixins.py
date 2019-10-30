# -*- coding: utf-8 -*-

import six

from sqlalchemy.orm import joinedload

from django.http import QueryDict
from django.test import SimpleTestCase

from rest_framework.fields import CharField, IntegerField
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.test import APIRequestFactory
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from rest_witchcraft.fields import SkippableField
from rest_witchcraft.mixins import ExpandableQuerySerializerMixin
from rest_witchcraft.serializers import ExpandableModelSerializer, ModelSerializer

from .models import Engine, Option, Owner, Vehicle, VehicleType, session
from .test_routers import UnAuthMixin


class DummySerializer(ModelSerializer):
    class Meta(object):
        session = session
        model = Vehicle
        fields = "__all__"


class VehicleOwnerStubSerializer(Serializer):
    id = IntegerField(source="_owner_id")


class VehicleSerializer(ExpandableModelSerializer):
    name = CharField()

    class Meta(object):
        session = session
        model = Vehicle
        expandable_fields = {
            "owner": VehicleOwnerStubSerializer(source="*", read_only=True),
            "options": SkippableField(),
            "name": CharField(),
        }
        fields = "__all__"


class DummyViewSet(ExpandableQuerySerializerMixin, GenericViewSet):
    serializer_class = DummySerializer

    def list(self, request, *args, **kwargs):
        return Response()


class ExpandableViewSet(UnAuthMixin, ExpandableQuerySerializerMixin, ModelViewSet):
    serializer_class = VehicleSerializer
    queryset = Vehicle.objects

    def list(self, request, *args, **kwargs):
        r = super().list(request, *args, **kwargs)
        r.data = {"query": six.text_type(self.get_queryset()), "results": r.data}
        return r


class TestDummyViewSet(SimpleTestCase):
    def test_no_queryset(self):
        self.assertIsNone(DummyViewSet().get_query_serializer())


class TestQuerySerializerMixin(SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.rf = APIRequestFactory()
        session.add(
            Vehicle(
                name="Test vehicle",
                type=VehicleType.car,
                engine=Engine(4, 1234, None, None),
                owner=Owner(id=1, first_name="Test", last_name="Owner"),
                options=[Option(name="Navigation"), Option(name="Rocket Engine")],
            )
        )
        session.flush()
        self.maxDiff = None

    def tearDown(self):
        super().tearDown()
        session.rollback()

    def test_invalid_query(self):
        view = ExpandableViewSet.as_view(actions={"get": "list"})

        self.assertEqual(view(self.rf.get("/")).status_code, 200)
        self.assertEqual(view(self.rf.get("/", {"expand": "owner"})).status_code, 200)
        self.assertEqual(view(self.rf.get("/", {"expand": "name"})).status_code, 200)
        self.assertEqual(view(self.rf.get("/", {"expand": "haha"})).status_code, 400)

    def test_no_query_serializer(self):
        view = ExpandableViewSet.as_view(actions={"get": "list"}, serializer_class=DummySerializer)

        self.assertEqual(view(self.rf.get("/")).status_code, 200)

    def test_eagerload_sql(self):
        view = ExpandableViewSet.as_view(actions={"get": "list"})

        self.assertNotIn("LEFT OUTER JOIN", view(self.rf.get("/")).data["query"])
        self.assertNotIn("LEFT OUTER JOIN", view(self.rf.get("/", {"expand": "name"})).data["query"])

        r = view(self.rf.get("/", {"expand": "owner"}))
        self.assertIn("LEFT OUTER JOIN", r.data["query"])
        self.assertEqual(r.data["query"].count("LEFT OUTER JOIN"), 1)
        self.assertNotIn("options", r.data["results"][0])

        # one to many should not add any more joins since selectinload is used
        r = view(self.rf.get("/", QueryDict("expand=owner&expand=options")))
        self.assertIn("LEFT OUTER JOIN", r.data["query"])
        self.assertEqual(r.data["query"].count("LEFT OUTER JOIN"), 1)
        self.assertIn("options", r.data["results"][0])

    def test_already_eagerload(self):
        view = ExpandableViewSet.as_view(
            actions={"get": "list"}, queryset=Vehicle.objects.options(joinedload(Vehicle.owner))
        )

        r = view(self.rf.get("/", {"expand": "owner"}))
        self.assertIn("LEFT OUTER JOIN", r.data["query"])
        # even if we add more joinedloads sqlalchemy should normalize them
        # as that exact path is already joined in base queryset
        self.assertEqual(r.data["query"].count("LEFT OUTER JOIN"), 1)
