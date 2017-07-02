# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import SimpleTestCase
from rest_witchcraft import utils
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class GetPkModel(Base):
    __tablename__ = 'getpk'

    pk1 = Column(String(), primary_key=True)


class GetPkCompositeModel(Base):
    __tablename__ = 'getpkcomposite'

    pk1 = Column(String(), primary_key=True)
    pk2 = Column(String(), primary_key=True)


class TestModelRoutes(SimpleTestCase):

    def test_get_pks_returns_none_when_no_pk_found(self):

        pks = utils.get_primary_keys(GetPkModel, {})

        self.assertIsNone(pks)

    def test_get_pks_returns_none_when_pk_none(self):

        pks = utils.get_primary_keys(GetPkModel, {'pk1': None})

        self.assertIsNone(pks)

    def test_get_pks_returns_none_when_one_pk_not_found(self):

        pks = utils.get_primary_keys(GetPkCompositeModel, {'pk1': 'a'})

        self.assertIsNone(pks)

    def test_get_pks_returns_none_when_one_pk_is_none(self):

        pks = utils.get_primary_keys(GetPkCompositeModel, {'pk1': 'a', 'pk2': None})

        self.assertIsNone(pks)
