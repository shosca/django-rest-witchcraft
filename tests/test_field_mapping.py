# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sqlalchemy as sqa
from django.test import SimpleTestCase
from rest_framework import fields
from rest_witchcraft import field_mapping
from rest_witchcraft.fields import CharMappingField, EnumField
from sqlalchemy.dialects import postgresql


class TestModelViewName(SimpleTestCase):

    def test_get_detail_view_name(self):

        name = field_mapping.get_detail_view_name(EnumField)

        self.assertEqual(name, 'enumfields-detail')


class TestGetFieldType(SimpleTestCase):

    def test_get_field_type_can_map_string_column(self):

        field = field_mapping.get_field_type(sqa.Column(sqa.String()))

        self.assertTrue(issubclass(field, fields.CharField))

    def test_get_field_type_can_map_int_column(self):

        field = field_mapping.get_field_type(sqa.Column(sqa.BigInteger()))

        self.assertTrue(issubclass(field, fields.IntegerField))

    def test_get_field_type_can_map_float_column(self):

        field = field_mapping.get_field_type(sqa.Column(sqa.Float()))

        self.assertTrue(issubclass(field, fields.FloatField))

    def test_get_field_type_can_map_decimal_column(self):

        column = sqa.Column(sqa.Numeric(asdecimal=True))
        field = field_mapping.get_field_type(column)

        self.assertTrue(issubclass(field, fields.DecimalField))

    def test_get_field_type_can_map_interval_column(self):

        column = sqa.Column(sqa.Interval())
        field = field_mapping.get_field_type(column)

        self.assertTrue(issubclass(field, fields.DurationField))

    def test_get_field_type_can_map_time_column(self):

        column = sqa.Column(sqa.Time())
        field = field_mapping.get_field_type(column)

        self.assertTrue(issubclass(field, fields.TimeField))

    def test_get_field_type_can_map_datetime_column(self):

        column = sqa.Column(sqa.DateTime())
        field = field_mapping.get_field_type(column)

        self.assertTrue(issubclass(field, fields.DateTimeField))

    def test_get_field_type_can_map_date_column(self):

        column = sqa.Column(sqa.Date())
        field = field_mapping.get_field_type(column)

        self.assertTrue(issubclass(field, fields.DateField))

    def test_get_field_type_can_map_bool_column(self):

        column = sqa.Column(sqa.Boolean(), nullable=False)
        field = field_mapping.get_field_type(column)

        self.assertTrue(issubclass(field, fields.BooleanField))

    def test_get_field_type_can_map_nullable_bool_column(self):

        column = sqa.Column(sqa.Boolean(), nullable=True)
        field = field_mapping.get_field_type(column)

        self.assertTrue(issubclass(field, fields.NullBooleanField))

    def test_get_field_type_can_map_pg_hstore_column(self):

        column = sqa.Column(postgresql.HSTORE())
        field = field_mapping.get_field_type(column)

        self.assertTrue(issubclass(field, CharMappingField))

    def test_get_field_type_can_map_pg_array_column(self):

        column = sqa.Column(postgresql.ARRAY(item_type=sqa.Integer()))
        field = field_mapping.get_field_type(column)

        self.assertTrue(issubclass(field, fields.ListField))
        self.assertIsInstance(field().child, fields.IntegerField)

    def test_get_field_type_pg_array_column_raises_when_item_type_not_found(self):

        class DummyType(object):
            python_type = None

        column = sqa.Column(postgresql.ARRAY(item_type=DummyType))

        with self.assertRaises(KeyError):
            field_mapping.get_field_type(column)
