# -*- coding: utf-8 -*-
from django.http import Http404
from rest_framework import viewsets

from .utils import get_primary_keys


class ModelViewSet(viewsets.ModelViewSet):

    def __init__(self, *args, **kwargs):
        super(ModelViewSet, self).__init__(*args, **kwargs)
        serializer_class = getattr(self, 'serializer_class', None)
        self.model = serializer_class.Meta.model

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' % (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}

        obj = queryset.get(get_primary_keys(self.model, filter_kwargs))

        if not obj:
            raise Http404('No %s matches the given query.' % self.model.__name__)

        return obj
