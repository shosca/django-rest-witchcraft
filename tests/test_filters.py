# -*- coding: utf-8 -*-

import coreschema

from django.test import RequestFactory

from rest_framework.settings import api_settings
from rest_framework.test import APISimpleTestCase

from rest_witchcraft.filters import SearchFilter
from rest_witchcraft.serializers import ModelSerializer
from rest_witchcraft.viewsets import ModelViewSet

from .models import Owner, session


class OwnerSerializer(ModelSerializer):
    class Meta:
        model = Owner
        session = session
        fields = "first_name", "last_name"


class OwnerViewSet(ModelViewSet):
    serializer_class = OwnerSerializer
    session = session
    queryset = property(lambda self: session.query(Owner))


class TestSearchFilters(APISimpleTestCase):
    factory = RequestFactory()

    def setUp(self):
        super().setUp()
        self.viewset_class = OwnerViewSet
        self.filter = SearchFilter()

        self.owner1 = Owner(id=1, first_name="Joe", last_name="Smith")
        self.owner2 = Owner(id=2, first_name="Jon", last_name="Snow")

        self.owners = [self.owner1, self.owner2]
        session.add_all(self.owners)
        session.flush()

    def tearDown(self):
        session.rollback()
        super().tearDown()

    def test_search_field(self):
        viewset = self.viewset_class()
        viewset.action_map = {"get": "list"}

        schema = self.filter.get_schema_fields(viewset)

        self.assertEqual(len(schema), 1)
        field = schema[0]

        self.assertEqual(field.name, api_settings.SEARCH_PARAM)
        self.assertFalse(field.required)
        self.assertEqual(field.location, "query")
        self.assertIsInstance(field.schema, coreschema.String)

        schema_ops = self.filter.get_schema_operation_parameters(viewset)
        self.assertDictEqual(
            {"test": schema_ops},
            {
                "test": [
                    {
                        "name": "search",
                        "required": False,
                        "in": "query",
                        "description": "A search term.",
                        "schema": {"type": "string"},
                    }
                ]
            },
        )

    def test_to_html(self):
        viewset = self.viewset_class()
        viewset.action_map = {"get": "list"}
        request = viewset.initialize_request(self.factory.get("/", {api_settings.SEARCH_PARAM: "jo"}))

        html = self.filter.to_html(request, viewset.get_queryset(), viewset)

        self.assertInHTML("<h2>Search</h2>", html)

        del viewset.__class__.search_fields
        html = self.filter.to_html(request, viewset.get_queryset(), viewset)
        self.assertEqual(html, "")

    def test_icontains(self):
        self.viewset_class.search_fields = ["first_name", "last_name"]

        viewset = self.viewset_class()
        viewset.action_map = {"get": "list"}
        request = viewset.initialize_request(self.factory.get("/"))

        query = self.filter.filter_queryset(request, viewset.get_queryset(), viewset)

        self.assertEqual(set(query.all()), set(self.owners))

        request = viewset.initialize_request(self.factory.get("/", {api_settings.SEARCH_PARAM: "jon"}))
        query = self.filter.filter_queryset(request, viewset.get_queryset(), viewset)

        self.assertEqual(set(query.all()), {self.owner2})

    def test_istartswith(self):
        self.viewset_class.search_fields = ["^first_name", "^last_name"]
        viewset = self.viewset_class()
        viewset.action_map = {"get": "list"}

        request = viewset.initialize_request(self.factory.get("/", {api_settings.SEARCH_PARAM: "jo"}))
        query = self.filter.filter_queryset(request, viewset.get_queryset(), viewset)
        self.assertEqual(set(query.all()), set(self.owners))

        request = viewset.initialize_request(self.factory.get("/", {api_settings.SEARCH_PARAM: "sno"}))
        query = self.filter.filter_queryset(request, viewset.get_queryset(), viewset)
        self.assertEqual(set(query.all()), {self.owner2})

    def test_iexact(self):
        self.viewset_class.search_fields = ["=first_name", "=last_name"]
        viewset = self.viewset_class()
        viewset.action_map = {"get": "list"}

        request = viewset.initialize_request(self.factory.get("/", {api_settings.SEARCH_PARAM: "sno"}))
        query = self.filter.filter_queryset(request, viewset.get_queryset(), viewset)
        self.assertEqual(set(query.all()), set())

        request = viewset.initialize_request(self.factory.get("/", {api_settings.SEARCH_PARAM: "snow"}))
        query = self.filter.filter_queryset(request, viewset.get_queryset(), viewset)
        self.assertEqual(set(query.all()), {self.owner2})

    def test_exact(self):
        self.viewset_class.search_fields = ["@first_name", "@last_name"]
        viewset = self.viewset_class()
        viewset.action_map = {"get": "list"}

        request = viewset.initialize_request(self.factory.get("/", {api_settings.SEARCH_PARAM: "snow"}))
        query = self.filter.filter_queryset(request, viewset.get_queryset(), viewset)
        self.assertEqual(set(query.all()), set())

        request = viewset.initialize_request(self.factory.get("/", {api_settings.SEARCH_PARAM: "Snow"}))
        query = self.filter.filter_queryset(request, viewset.get_queryset(), viewset)
        self.assertEqual(set(query.all()), {self.owner2})
