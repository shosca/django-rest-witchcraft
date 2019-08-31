# -*- coding: utf-8 -*-
"""
Provides generic filtering backends that can be used to filter the results
returned by list views.
"""


from sqlalchemy import func, or_
from sqlalchemy.sql import operators

from django.template import loader
from django.utils.encoding import force_text
from django.utils.translation import gettext_lazy

from rest_framework.compat import coreapi, coreschema
from rest_framework.filters import BaseFilterBackend
from rest_framework.settings import api_settings


class SearchFilter(BaseFilterBackend):
    search_param = api_settings.SEARCH_PARAM
    template = "rest_framework/filters/search.html"
    lookup_prefixes = {
        "": lambda c, x: operators.ilike_op(c, "%{0}%".format(x)),  # icontains
        "^": lambda c, x: c.ilike(x.replace("%", "%%") + "%"),  # istartswith
        "=": lambda c, x: func.lower(c) == func.lower(x),  # iequals
        "@": operators.eq,  # equals
    }
    search_title = gettext_lazy("Search")
    search_description = gettext_lazy("A search term.")

    def get_schema_fields(self, view):
        assert coreapi is not None, "coreapi must be installed to use `get_schema_fields()`"
        assert coreschema is not None, "coreschema must be installed to use `get_schema_fields()`"
        return [
            coreapi.Field(
                name=self.search_param,
                required=False,
                location="query",
                schema=coreschema.String(
                    title=force_text(self.search_title), description=force_text(self.search_description)
                ),
            )
        ]

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": self.search_param,
                "required": False,
                "in": "query",
                "description": force_text(self.search_description),
                "schema": {"type": "string"},
            }
        ]

    def get_search_fields(self, view, request):
        return getattr(view, "search_fields", None)

    def get_search_terms(self, request):
        params = request.query_params.get(self.search_param, "")
        params = params.replace("\x00", "")  # strip null characters
        params = params.replace(",", " ")
        return params.split()

    def to_html(self, request, queryset, view):
        if not getattr(view, "search_fields", None):
            return ""

        term = self.get_search_terms(request)
        term = term[0] if term else ""
        context = {"param": self.search_param, "term": term}
        template = loader.get_template(self.template)
        return template.render(context)

    def filter_queryset(self, request, queryset, view):
        search_fields = self.get_search_fields(view, request)
        search_terms = self.get_search_terms(request)

        if not search_fields or not search_terms:
            return queryset

        model = view.get_model()

        expressions = []
        for field in search_fields:
            for term in search_terms:
                expr = self.get_expression(model, field, term)
                if expr is not None:
                    expressions.append(expr)

        return queryset.filter(or_(*expressions))

    def get_expression(self, model, field, term):
        op = self.lookup_prefixes[""]
        if field[0] in self.lookup_prefixes:
            op = self.lookup_prefixes[field[0]]
            field = field[1:]

        expr = op(getattr(model, field), term)
        return expr
