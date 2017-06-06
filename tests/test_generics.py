# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import Http404
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory
from rest_witchcraft import serializers, viewsets
from sqlalchemy import Column, create_engine, orm, types
from sqlalchemy.ext.declarative import declarative_base

factory = APIRequestFactory()

engine = create_engine('sqlite://')
session = orm.scoped_session(orm.sessionmaker(bind=engine))
Base = declarative_base()
Base.query = session.query_property()


class RouterTestModel(Base):
    __tablename__ = 'routertest'
    id = Column(types.Integer(), default=3, primary_key=True)
    text = Column(types.String(length=200))


Base.metadata.create_all(engine)


class RouterTestModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = RouterTestModel
        session = session
        fields = '__all__'


class TestModelRoutes(SimpleTestCase):

    def test_get_model_using_queryset(self):

        class RouterTestViewSet(viewsets.ModelViewSet):
            queryset = RouterTestModel.query
            serializer_class = RouterTestModelSerializer

        model = RouterTestViewSet.get_model()

        self.assertEqual(model, RouterTestModel)

    def test_get_model_using_serializer(self):

        class RouterTestViewSet(viewsets.ModelViewSet):
            serializer_class = RouterTestModelSerializer

        model = RouterTestViewSet.get_model()

        self.assertEqual(model, RouterTestModel)

    def test_get_model_fails_with_assert_error(self):

        class RouterTestViewSet(viewsets.ModelViewSet):
            pass

        with self.assertRaises(AssertionError):
            RouterTestViewSet.get_model()

    def test_get_object_raises_404(self):

        class RouterTestViewSet(viewsets.ModelViewSet):
            queryset = RouterTestModel.query
            serializer_class = RouterTestModelSerializer

        viewset = RouterTestViewSet()
        viewset.kwargs = {'id': 1}

        with self.assertRaises(Http404):
            viewset.get_object()
