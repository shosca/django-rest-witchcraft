# -*- coding: utf-8 -*-


def get_detail_view_name(model):
    """
    Given a model class, return the view name to use for URL relationships
    that rever to instances of the model.
    """
    return '{}s-detail'.format(model.__name__.lower())


def get_url_kwargs(model):
    field_kwargs = {'read_only': True}

    return field_kwargs
