# -*- coding: utf-8 -*-

from sqlalchemy.exc import InvalidRequestError

from django.http import Http404

from django_sorcery.db.meta import model_info
from django_sorcery.utils import suppress

from rest_framework import generics


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

        with suppress(AttributeError, InvalidRequestError):
            model = cls.queryset._only_entity_zero().class_

        if model:
            return model

        with suppress(AttributeError):
            model = cls.serializer_class.Meta.model

        assert model is not None, (
            "Couldn't figure out the model for {viewset} attribute, either provide a"
            "queryset or a serializer with a Meta.model".format(viewset=cls.__name__)
        )

        return model

    def get_session(self):
        """
        Returns the session
        """
        queryset = self.get_queryset()
        return queryset.session

    def get_object(self):
        """
        Returns the object the view is displaying.

        We ignore the `lookup_field` and `lookup_url_kwarg` values
        only when tere are multiple primary keys
        """
        queryset = self.get_queryset()
        model = self.get_model()
        info = model_info(model)
        kwargs = self.kwargs.copy()

        # we want to honor DRF lookup_field and lookup_url_kwarg API
        # but only if they are defined and there is single primary key.
        # When there are multiple, all bets are off so we restrict url kwargs
        # to model column names
        if len(info.primary_keys) == 1:
            lookup_field = self.lookup_field
            lookup_url_kwarg = self.lookup_url_kwarg or lookup_field

            kwargs[lookup_field] = kwargs.pop(lookup_url_kwarg)

        obj = queryset.get(info.primary_keys_from_dict(kwargs))

        if not obj:
            raise Http404("No %s matches the given query." % model.__name__)

        return obj
