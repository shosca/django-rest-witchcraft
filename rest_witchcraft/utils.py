# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from itertools import chain

from rest_framework.serializers import ValidationError
from rest_framework.settings import api_settings

from django.core.exceptions import NON_FIELD_ERRORS


def _django_to_drf(e):
    if hasattr(e, "error_dict"):
        return {
            k if not k == NON_FIELD_ERRORS else api_settings.NON_FIELD_ERRORS_KEY: _django_to_drf(v)
            for k, v in e.error_dict.items()
        }
    elif hasattr(e, "error_list"):
        return e.messages
    elif isinstance(e, dict):
        return {
            k if not k == NON_FIELD_ERRORS else api_settings.NON_FIELD_ERRORS_KEY: _django_to_drf(v)
            for k, v in e.items()
        }
    elif isinstance(e, list):
        return list(chain(*[_django_to_drf(i) for i in e]))
    return e


def django_to_drf_validation_error(e):
    return ValidationError(
        _django_to_drf(e) if hasattr(e, "error_dict") else {api_settings.NON_FIELD_ERRORS_KEY: e.messages}
    )
