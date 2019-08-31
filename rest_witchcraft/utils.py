# -*- coding: utf-8 -*-

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError as DjangoValidationError

from rest_framework.serializers import ValidationError
from rest_framework.settings import api_settings


def _django_to_drf(e):
    if hasattr(e, "error_dict") or isinstance(e, dict):
        return {
            k if not k == NON_FIELD_ERRORS else api_settings.NON_FIELD_ERRORS_KEY: _django_to_drf(v)
            for k, v in getattr(e, "error_dict", e).items()
        }
    elif hasattr(e, "error_list"):
        return e.messages
    elif isinstance(e, list):
        errors = []
        for j in e:
            if isinstance(j, DjangoValidationError):
                errors += _django_to_drf(j)
            else:
                errors.append(_django_to_drf(j))
        return errors
    return e


def django_to_drf_validation_error(e):
    return ValidationError(
        _django_to_drf(e) if hasattr(e, "error_dict") else {api_settings.NON_FIELD_ERRORS_KEY: e.messages}
    )
