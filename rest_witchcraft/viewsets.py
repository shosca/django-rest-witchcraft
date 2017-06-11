# -*- coding: utf-8 -*-
from rest_framework import mixins, viewsets

from .generics import GenericAPIView
from .mixins import DestroyModelMixin


class GenericViewSet(viewsets.ViewSetMixin, GenericAPIView):
    """
    The GenericViewSet class does not provide any actions by default, but does include the base set of generic view
    behavior, such as the `get_object` and `get_queryset` methods.
    """


class ReadOnlyViewModelViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    """
    A viewset that provides default `list()` and `retrieve()` actions.
    """


class ModelViewSet(
    mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, DestroyModelMixin,
    mixins.ListModelMixin, GenericViewSet
):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`, `partial_update()`, `destroy()` and `list()`
    actions.
    """
