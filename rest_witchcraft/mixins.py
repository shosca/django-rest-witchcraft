# -*- coding: utf-8 -*-
from rest_framework import mixins


class DestroyModelMixin(mixins.DestroyModelMixin):
    """
    Deletes a model instance
    """

    def perform_destroy(self, instance):
        session = self.get_session()
        session.delete(instance)
