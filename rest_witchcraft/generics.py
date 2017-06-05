# -*- coding: utf-8 -*-
from django.http import Http404
from rest_framework import generics

from .utils import get_primary_keys


class GenericAPIView(generics.GenericAPIView):
    """
    Base class for sqlalchemy specific views
    """

    def get_object(self):
        """
        Returns the object the view is displaying.

        You may want to override this if you need to provide non-standard queryset lookups.  Eg if objects are
        referenced using multiple keyword arguments in the url conf.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' % (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}

        model = self.get_serializer_class().Meta.model

        obj = queryset.get(get_primary_keys(model, filter_kwargs))

        if not obj:
            raise Http404('No %s matches the given query.' % self.model.__name__)

        return obj
