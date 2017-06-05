# -*- coding: utf-8 -*-
from django.http import Http404
from rest_framework import generics
from sqlalchemy.exc import InvalidRequestError

from .utils import get_primary_keys, suppress


class GenericAPIView(generics.GenericAPIView):
    """
    Base class for sqlalchemy specific views
    """

    @classmethod
    def get_model(cls):
        """
        Returns the model class
        """
        model = None

        with suppress(InvalidRequestError):
            model = cls.queryset._only_entity_zero().class_

        if model:
            return model

        with suppress(AttributeError):
            model = cls.serializer_class.Meta.model

        if model:
            return model

    def get_object(self):
        """
        Returns the object the view is displaying.

        We ignore the `lookup_field` and `lookup_url_kwarg` values
        """
        queryset = self.get_queryset()

        obj = queryset.get(get_primary_keys(self.get_model(), self.kwargs))

        if not obj:
            raise Http404('No %s matches the given query.' % self.model.__name__)

        return obj
