# -*- coding: utf-8 -*-

from django_sorcery.db import meta

from rest_framework import routers


class DefaultRouter(routers.DefaultRouter):
    def get_default_base_name(self, viewset):

        model = getattr(viewset, "get_model", lambda: None)()

        assert model is not None, (
            "`base_name` argument not specified, and could not automatically determine the name from the viewset, "
            "as either queryset is is missing or is not a sqlalchemy query, or the serializer_class is not a "
            "sqlalchemy model serializer"
        )

        return model.__name__.lower()

    # for backwards compatibility DRF<3.9
    get_default_basename = get_default_base_name

    def get_lookup_regex(self, viewset, lookup_prefix=""):
        """
        Given a viewset, return the portion of the url regex that is used to match against a single instance.

        Can be overwritten by providing a `lookup_url_regex` on the viewset.
        """

        lookup_url_regex = getattr(viewset, "lookup_url_regex", None)
        if lookup_url_regex:
            return lookup_url_regex

        model = getattr(viewset, "get_model", lambda: None)()
        if model:
            info = meta.model_info(model)
            base_regex = "(?P<{lookup_prefix}{lookup_url_kwarg}>{lookup_value})"

            lookup_keys = [getattr(viewset, "lookup_url_kwarg", None) or getattr(viewset, "lookup_field", None)]
            if not lookup_keys[0] or len(info.primary_keys) > 1:
                lookup_keys = list(info.primary_keys)

            regexes = []
            for key in lookup_keys:
                regexes.append(
                    base_regex.format(lookup_prefix=lookup_prefix, lookup_url_kwarg=key, lookup_value="[^/.]+")
                )

            return "/".join(regexes)

        return super().get_lookup_regex(viewset, lookup_prefix)
