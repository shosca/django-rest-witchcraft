# -*- coding: utf-8 -*-
import unittest
from collections import OrderedDict
from decimal import Decimal

from django.core.exceptions import ImproperlyConfigured
from rest_framework import fields
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ListSerializer
from rest_framework.settings import api_settings
from rest_witchcraft.utils import _column_info
from sqlalchemy import Column, types

from .models import (  # noqa # isort:skip
    COLORS, Engine, Option, Owner, Vehicle, VehicleOther, VehicleType, session
)

from rest_witchcraft.serializers import (  # noqa # isort:skip
    BaseSerializer, CompositeSerializer,
    ModelSerializer, model_info)


class TestModelSerializer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestModelSerializer, cls).setUpClass()
        session.add(Owner(id=1, name='Test owner'))
        session.add_all(
            [
                Option(id=1, name='Option 1'),
                Option(id=2, name='Option 2'),
                Option(id=3, name='Option 3'),
                Option(id=4, name='Option 4'),
            ]
        )
        session.commit()

    def tearDown(self):
        super(TestModelSerializer, self).tearDown()
        session.rollback()

    def test_cannot_initialize_without_a_meta(self):

        class VehicleSerializer(ModelSerializer):
            pass

        with self.assertRaises(AssertionError):
            VehicleSerializer()

    def test_cannot_initialize_without_a_session(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                pass

        with self.assertRaises(AssertionError):
            VehicleSerializer()

    def test_cannot_initialize_without_a_model_with_session_meta(self):

        class VehicleSerializer(ModelSerializer):

            class Meta(object):
                session = session

        with self.assertRaises(AttributeError):
            VehicleSerializer()

    def test_cannot_initialize_without_a_model_with_session_kwarg(self):

        class VehicleSerializer(ModelSerializer):

            class Meta(object):
                pass

        with self.assertRaises(AttributeError):
            VehicleSerializer(session=session)

    def test_get_fields_sets_url_field_name_when_missing(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                exclude = ('name', )

        serializer = VehicleSerializer()
        serializer.get_fields()

        self.assertEqual(serializer.url_field_name, api_settings.URL_FIELD_NAME)

    def test_raises_type_error_if_fields_is_not_a_list_or_tuple(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = 'name'

        serializer = VehicleSerializer()

        with self.assertRaises(TypeError):
            serializer.get_fields()

    def test_raises_type_error_if_exclude_is_not_a_list_or_tuple(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                exclude = 'name'

        serializer = VehicleSerializer()

        with self.assertRaises(TypeError):
            serializer.get_fields()

    def test_get_default_field_names_should_get_all_field_names(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = ('id', 'name')

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        field_names = serializer.get_default_field_names([], info)
        self.assertEqual(
            set(field_names),
            set(
                [
                    Vehicle.created_at.key,
                    Vehicle.engine.key,
                    Vehicle.id.key,
                    Vehicle.name.key,
                    Vehicle.options.key,
                    Vehicle.other.key,
                    Vehicle.owner.key,
                    Vehicle.paint.key,
                    Vehicle.type.key,
                    'url',
                ]
            )
        )

    def test_get_field_names_with_include(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = ('id', 'name')

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        field_names = serializer.get_field_names([], info)
        self.assertEqual(set(field_names), set([
            Vehicle.id.key,
            Vehicle.name.key,
        ]))

    def test_get_field_names_with_exclude(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                exclude = ('type', 'options')

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        field_names = serializer.get_field_names([], info)
        self.assertEqual(
            set(field_names),
            set(
                [
                    Vehicle.created_at.key, Vehicle.engine.key, Vehicle.id.key, Vehicle.name.key, Vehicle.other.key,
                    Vehicle.owner.key, Vehicle.paint.key, 'url'
                ]
            )
        )

    def test_generate_all_fields(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = '__all__'

        serializer = VehicleSerializer()
        generated_fields = serializer.get_fields()

        self.assertIn(Vehicle.id.key, generated_fields)
        self.assertIn(Vehicle.type.key, generated_fields)
        self.assertIn(Vehicle.name.key, generated_fields)
        self.assertIn(Vehicle.engine.key, generated_fields)
        self.assertIn(Vehicle.owner.key, generated_fields)
        self.assertIn(Vehicle.options.key, generated_fields)

    def test_declared_field(self):

        class VehicleSerializer(ModelSerializer):
            name = fields.ChoiceField(choices=['a', 'b'])

            class Meta:
                model = Vehicle
                session = session
                fields = '__all__'

        serializer = VehicleSerializer()
        generated_fields = serializer.get_fields()

        self.assertIsInstance(generated_fields['name'], fields.ChoiceField)

    def test_get_field_names_includes_all_required_fields(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = ('id', 'name')

        serializer = VehicleSerializer()
        info = model_info(Vehicle)

        with self.assertRaises(AssertionError):
            serializer.get_field_names(['type'], info)

    def test_include_extra_kwargs(self):

        serializer = BaseSerializer()

        kwargs = {}
        extra_kwargs = {}

        kwargs = serializer.include_extra_kwargs(kwargs, extra_kwargs)

        self.assertEqual(kwargs, {})

    def test_include_extra_kwargs_filter_when_read_only(self):

        serializer = BaseSerializer()

        kwargs = {
            'allow_blank': True,
            'allow_null': True,
            'default': True,
            'max_length': 255,
            'max_value': 255,
            'min_length': 0,
            'min_value': 0,
            'queryset': None,
            'required': True,
            'validators': None,
        }
        extra_kwargs = {'read_only': True}

        kwargs = serializer.include_extra_kwargs(kwargs, extra_kwargs)

        self.assertEqual(kwargs, {'read_only': True})

    def test_include_extra_kwargs_filter_required_when_default_provided(self):

        serializer = BaseSerializer()

        kwargs = {
            'required': False,
        }
        extra_kwargs = {'default': True}

        kwargs = serializer.include_extra_kwargs(kwargs, extra_kwargs)

        self.assertEqual(kwargs, {'default': True})

    def test_base_serializer_raises_on_create(self):

        serializer = BaseSerializer()

        with self.assertRaises(NotImplementedError):
            serializer.create({})

    def test_base_serializer_raises_on_update(self):

        serializer = BaseSerializer()

        with self.assertRaises(NotImplementedError):
            serializer.update(None, {})

    def test_get_extra_kwargs_with_no_extra_kwargs(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = ('id', 'name')

        serializer = VehicleSerializer()
        extra_kwargs = serializer.get_extra_kwargs()
        self.assertEqual(extra_kwargs, {})

    def test_get_extra_kwargs_with_extra_kwargs(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = ('id', 'name')
                extra_kwargs = {'name': {'read_only': True}}

        serializer = VehicleSerializer()
        extra_kwargs = serializer.get_extra_kwargs()
        self.assertEqual(extra_kwargs, {'name': {'read_only': True}})

    def test_get_extra_kwargs_with_read_only_fields(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = ('id', 'name')
                read_only_fields = ('id', 'name')

        serializer = VehicleSerializer()
        extra_kwargs = serializer.get_extra_kwargs()
        self.assertEqual(extra_kwargs, {'id': {'read_only': True}, 'name': {'read_only': True}})

    def test_get_extra_kwargs_with_read_only_fields_as_string(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = ('id', 'name')
                read_only_fields = 'id'

        with self.assertRaises(TypeError):
            VehicleSerializer()

    def test_build_standard_integer_field(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = '__all__'

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        field = serializer.build_field(Vehicle.id.key, info, 0)

        self.assertEqual(field.help_text, Vehicle.id.doc)
        self.assertEqual(field.label, 'Id')
        self.assertFalse(field.allow_null)
        self.assertIsInstance(field, fields.IntegerField)
        self.assertTrue(field.required)

    def test_build_standard_char_field(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = '__all__'

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        field = serializer.build_field(Vehicle.name.key, info, 0)

        self.assertEqual(field.help_text, Vehicle.name.doc)
        self.assertEqual(field.label, 'Name')
        self.assertFalse(field.required)
        self.assertIsInstance(field, fields.CharField)
        self.assertTrue(field.allow_null)

    def test_build_enum_field(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = ('type', )

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        field = serializer.build_field(Vehicle.type.key, info, 0)

        self.assertEqual(field.help_text, Vehicle.type.doc)
        self.assertEqual(field.label, 'Type')
        self.assertTrue(field.required)
        self.assertIsInstance(field, fields.ChoiceField)
        self.assertFalse(field.allow_null)

    def test_build_choice_field(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = ('paint', )

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        field = serializer.build_field(Vehicle.paint.key, info, 0)

        self.assertEqual(field.help_text, Vehicle.paint.doc)
        self.assertEqual(field.label, 'Paint')
        self.assertFalse(field.required)
        self.assertIsInstance(field, fields.ChoiceField)
        self.assertEqual(field.choices, OrderedDict([(color, color) for color in COLORS]))
        self.assertTrue(field.allow_null)

    def test_fail_when_a_field_type_not_found(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = ('paint', )

        serializer = VehicleSerializer()
        info = _column_info(None, Column('test', types.JSON()))

        with self.assertRaises(KeyError):
            serializer.build_standard_field('test', info)

    def test_build_composite_field(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = '__all__'

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        field = serializer.build_field(Vehicle.engine.key, info, 0)

        self.assertIsInstance(field, CompositeSerializer)
        self.assertEqual(len(field.fields), 4)

    def test_build_property_field(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = '__all__'

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        field = serializer.build_field('lower_name', info, 0)

        self.assertIsInstance(field, fields.ReadOnlyField)

    def test_build_unknows_field(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = '__all__'

        serializer = VehicleSerializer()
        info = model_info(Vehicle)

        with self.assertRaises(ImproperlyConfigured):
            serializer.build_field('abcde', info, 0)

    def test_build_one_to_many_relationship_field(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = '__all__'

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        nested_serializer = serializer.build_field(Vehicle.owner.key, info, 0)

        self.assertIsNotNone(nested_serializer)
        self.assertIsInstance(nested_serializer, ModelSerializer)
        self.assertEqual(len(nested_serializer.fields), 2)

    def test_build_one_to_many_relationship_field_with_nested_updates_disabled(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = '__all__'
                extra_kwargs = {'owner': {'allow_nested_updates': False}}

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        nested_serializer = serializer.build_field(Vehicle.owner.key, info, 0)

        self.assertIsNotNone(nested_serializer)
        self.assertIsInstance(nested_serializer, ModelSerializer)
        self.assertEqual(len(nested_serializer.fields), 2)
        self.assertTrue(nested_serializer.fields['name'].read_only)

    def test_build_serializer_with_depth(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = '__all__'
                depth = 3

        serializer = VehicleSerializer()

        self.assertEqual(len(serializer.fields), 10)
        self.assertEqual(
            set(serializer.fields.keys()),
            set(
                [
                    Vehicle.created_at.key,
                    Vehicle.engine.key,
                    Vehicle.id.key,
                    Vehicle.name.key,
                    Vehicle.options.key,
                    Vehicle.other.key,
                    Vehicle.owner.key,
                    Vehicle.paint.key,
                    Vehicle.type.key,
                    'url',
                ]
            )
        )

        engine_serializer = serializer.fields['engine']
        self.assertEqual(len(engine_serializer.fields), 4)
        self.assertEqual(set(engine_serializer.fields.keys()), set(['type_', 'displacement', 'fuel_type', 'cylinders']))

        owner_serializer = serializer.fields['owner']
        self.assertEqual(len(owner_serializer.fields), 2)
        self.assertEqual(set(owner_serializer.fields.keys()), set(['id', 'name']))

        options_serializer = serializer.fields['options']
        self.assertTrue(options_serializer.many)
        self.assertIsInstance(options_serializer, ListSerializer)

        option_serializer = options_serializer.child
        self.assertEqual(len(option_serializer.fields), 2)
        self.assertEqual(set(option_serializer.fields.keys()), set(['id', 'name']))

    def test_serializer_zero_depth_invalid_error_message(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = '__all__'

        serializer = VehicleSerializer(data={})

        self.assertFalse(serializer.is_valid())

        self.assertDictEqual(dict(serializer.errors), {'type': ['This field is required.']})

    def test_serializer_zero_depth_post_basic_validation(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = '__all__'
                extra_kwargs = {'other': {'required': False}}

        data = {
            'name': 'Test vehicle',
            'one': 'Two',
            'type': 'bus',
            'engine': {
                'displacement': 1234,
                'cylinders': 4,
            },
            'owner': {
                'id': 1
            },
            'options': [],
        }
        serializer = VehicleSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        self.assertDictEqual(
            dict(serializer.validated_data), {
                'name': 'Test vehicle',
                'type': VehicleType['bus'],
                'engine': {
                    'displacement': Decimal('1234.00'),
                    'cylinders': 4,
                },
                'owner': {
                    'id': 1
                },
                'options': []
            }
        )

    def test_serializer_create(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = '__all__'
                extra_kwargs = {'other': {'required': False, 'allow_create': False}}

        data = {
            'name': 'Test vehicle',
            'one': 'Two',
            'type': 'bus',
            'engine': {
                'displacement': 1234,
                'cylinders': 4,
            },
            'owner': {
                'id': 1
            },
            'options': []
        }

        serializer = VehicleSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.save()

        self.assertEqual(vehicle.name, data['name'])
        self.assertEqual(vehicle.type, VehicleType[data['type']])
        self.assertEqual(vehicle.engine.cylinders, data['engine']['cylinders'])
        self.assertEqual(vehicle.engine.displacement, data['engine']['displacement'])
        self.assertEqual(vehicle.engine.fuel_type, None)
        self.assertEqual(vehicle.engine.type_, None)
        self.assertEqual(vehicle.owner.id, data['owner']['id'])
        self.assertEqual(vehicle.owner.name, 'Test owner')
        self.assertEqual(vehicle.options, data['options'])

    def test_post_update(self):

        vehicle = Vehicle(
            name='Test vehicle', type=VehicleType.bus, engine=Engine(4, 1234, None, None),
            owner=session.query(Owner).get(1)
        )

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = '__all__'
                extra_kwargs = {'other': {'required': False, 'allow_create': True, 'allow_nested_updates': True}}

        data = {
            'name': 'Another test vechicle',
            'one': 'Two',
            'type': 'car',
            'engine': {
                'displacement': 4321,
                'cylinders': 2,
                'type_': 'banana',
                'fuel_type': 'petrol',
            },
            'owner': {
                'id': 1
            },
            'options': [],
            'other': {
                'advertising_cost': 4321
            }
        }

        serializer = VehicleSerializer(instance=vehicle, data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.save()

        self.assertEqual(vehicle.name, data['name'])
        self.assertEqual(vehicle.type, VehicleType[data['type']])
        self.assertEqual(vehicle.engine.cylinders, data['engine']['cylinders'])
        self.assertEqual(vehicle.engine.displacement, data['engine']['displacement'])
        self.assertEqual(vehicle.engine.fuel_type, data['engine']['fuel_type'])
        self.assertEqual(vehicle.engine.type_, data['engine']['type_'])
        self.assertEqual(vehicle.owner.id, data['owner']['id'])
        self.assertEqual(vehicle.owner.name, 'Test owner')
        self.assertEqual(vehicle.options, data['options'])
        self.assertEqual(vehicle.other.advertising_cost, 4321)

    def test_patch_update(self):

        vehicle = Vehicle(
            name='Test vehicle', type=VehicleType.bus, engine=Engine(4, 1234, None, None),
            owner=session.query(Owner).get(1), other=VehicleOther(advertising_cost=4321)
        )

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = '__all__'
                extra_kwargs = {'other': {'required': False, 'allow_create': True, 'allow_nested_updates': True}}

        data = {'other': {'advertising_cost': 1234}}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.save()

        self.assertEqual(vehicle.other.advertising_cost, data['other']['advertising_cost'])

    def test_composite_serializer_can_create(self):

        class EngineSerializer(CompositeSerializer):

            class Meta:
                composite = Vehicle.engine

        data = {
            'cylinders': 2,
            'displacement': 1234,
            'fuel_type': 'petrol',
            'type_': 'banana',
        }

        serializer = EngineSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        engine = serializer.save()

        self.assertIsInstance(engine, Engine)
        self.assertEqual(engine.cylinders, 2)
        self.assertEqual(engine.displacement, 1234)
        self.assertEqual(engine.fuel_type, 'petrol')
        self.assertEqual(engine.type_, 'banana')

    def test_composite_serializer_can_update(self):

        class EngineSerializer(CompositeSerializer):

            class Meta:
                composite = Vehicle.engine

        data = {
            'cylinders': 2,
            'displacement': 1234,
            'fuel_type': 'diesel',
            'type_': 'banana',
        }
        engine = Engine(4, 2345, 'apple', 'petrol')

        serializer = EngineSerializer(engine, data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        engine = serializer.save()

        self.assertIsInstance(engine, Engine)
        self.assertEqual(engine.cylinders, 2)
        self.assertEqual(engine.displacement, 1234)
        self.assertEqual(engine.fuel_type, 'diesel')
        self.assertEqual(engine.type_, 'banana')

    def test_composite_serializer_can_update_patch(self):

        class EngineSerializer(CompositeSerializer):

            class Meta:
                composite = Vehicle.engine

        data = {
            'cylinders': 2,
        }
        engine = Engine(4, 2345, 'apple', 'petrol')

        serializer = EngineSerializer(engine, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        engine = serializer.save()

        self.assertIsInstance(engine, Engine)
        self.assertEqual(engine.cylinders, 2)
        self.assertEqual(engine.displacement, 2345)
        self.assertEqual(engine.fuel_type, 'petrol')
        self.assertEqual(engine.type_, 'apple')

    def test_composite_serializer_can_use_custom_setter(self):

        class EngineSerializer(CompositeSerializer):

            class Meta:
                composite = Vehicle.engine

            def set_cylinders(self, instance, field, value):
                self.called = True
                instance.cylinders = value

        data = {
            'cylinders': 2,
        }
        engine = Engine(4, 2345, 'apple', 'petrol')

        serializer = EngineSerializer(engine, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        engine = serializer.save()

        self.assertTrue(serializer.called)

    def test_composite_serializer_can_handle_errors_during_update(self):

        class EngineSerializer(CompositeSerializer):

            class Meta:
                composite = Vehicle.engine

            def set_cylinders(self, instance, field, value):
                assert False, 'Some error'

        data = {
            'cylinders': 2,
        }
        engine = Engine(4, 2345, 'apple', 'petrol')

        serializer = EngineSerializer(engine, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        with self.assertRaises(ValidationError):
            engine = serializer.save()

    def test_patch_update_to_list_with_empty_list_clears_it(self):
        vehicle = Vehicle(
            name='Test vehicle', type=VehicleType.bus, engine=Engine(4, 1234, None,
                                                                     None), owner=session.query(Owner).get(1),
            other=VehicleOther(advertising_cost=4321), options=session.query(Option).all()
        )

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = ('options', )

        data = {'options': []}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.save()

        self.assertEqual(len(vehicle.options), 0)

    def test_patch_update_to_list_with_new_list(self):
        vehicle = Vehicle(
            name='Test vehicle', type=VehicleType.bus, engine=Engine(4, 1234, None,
                                                                     None), owner=session.query(Owner).get(1),
            other=VehicleOther(advertising_cost=4321), options=session.query(Option).filter(Option.id.in_([1, 2])).all()
        )

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = ('options', )

        data = {'options': [{'id': 3}, {'id': 4}]}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.update(vehicle, serializer.validated_data)

        self.assertEqual(len(vehicle.options), 2)
        self.assertEqual(set([v.id for v in vehicle.options]), set([3, 4]))

    def test_patch_update_to_list_with_new_list_with_nested(self):
        vehicle = Vehicle(
            name='Test vehicle', type=VehicleType.bus, engine=Engine(4, 1234, None,
                                                                     None), owner=session.query(Owner).get(1),
            other=VehicleOther(advertising_cost=4321), options=session.query(Option).filter(Option.id.in_([1, 2])).all()
        )

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = ('options', )
                extra_kwargs = {'options': {'allow_nested_updates': True}}

        data = {'options': [{'id': 1, 'name': 'Test 1'}, {'id': 2, 'name': 'Test 2'}]}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.update(vehicle, serializer.validated_data)

        self.assertEqual([option.id for option in vehicle.options], [1, 2])
        self.assertEqual([option.name for option in vehicle.options], ['Test 1', 'Test 2'])

    def test_patch_update_to_list_with_new_list_with_nested_raises_for_a_bad_pk(self):
        vehicle = Vehicle(
            name='Test vehicle', type=VehicleType.bus, engine=Engine(4, 1234, None,
                                                                     None), owner=session.query(Owner).get(1),
            other=VehicleOther(advertising_cost=4321), options=session.query(Option).filter(Option.id.in_([1, 2])).all()
        )

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = ('options', )
                extra_kwargs = {'options': {'allow_nested_updates': True}}

        data = {'options': [{'id': 1, 'name': 'Test 1'}, {'id': 5, 'name': 'Test 5'}]}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        with self.assertRaises(ValidationError):
            serializer.update(vehicle, serializer.validated_data)

    def test_update_generates_validation_error_when_required_many_to_one_instance_not_found(self):
        vehicle = Vehicle(
            name='Test vehicle', type=VehicleType.bus, engine=Engine(4, 1234, None,
                                                                     None), owner=session.query(Owner).get(1),
            other=VehicleOther(advertising_cost=4321), options=session.query(Option).filter(Option.id.in_([1, 2])).all()
        )

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = ('owner', )
                extra_kwargs = {'owner': {'allow_null': False}}

        data = {'owner': {'id': 1234}}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        with self.assertRaises(ValidationError):
            serializer.update(vehicle, serializer.validated_data)

    def test_update_calls_custom_setter(self):

        class VehicleSerializer(ModelSerializer):

            class Meta:
                model = Vehicle
                session = session
                fields = ('name', )

            def set_name(self, instance, field, value):
                self._set_name_called = True

        vehicle = Vehicle(
            name='Test vehicle', type=VehicleType.bus, engine=Engine(4, 1234, None,
                                                                     None), owner=session.query(Owner).get(1),
            other=VehicleOther(advertising_cost=4321), options=session.query(Option).filter(Option.id.in_([1, 2])).all()
        )

        data = {'name': 'Bob Loblaw'}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        serializer.update(vehicle, serializer.validated_data)
        self.assertTrue(serializer._set_name_called)

    def test_get_object_can_get_object(self):

        class OwnerSerializer(ModelSerializer):

            class Meta:
                model = Owner
                session = session
                fields = '__all__'

        serializer = OwnerSerializer()

        instance = serializer.get_object({'id': 1})

        self.assertIsNotNone(instance)

    def test_get_object_raise_when_not_found(self):

        class OwnerSerializer(ModelSerializer):

            class Meta:
                model = Owner
                session = session
                fields = '__all__'

        serializer = OwnerSerializer()

        with self.assertRaises(ValidationError):
            serializer.get_object({'id': 999})

    def test_get_object_allows_null_when_not_found(self):

        class OwnerSerializer(ModelSerializer):

            class Meta:
                model = Owner
                session = session
                fields = '__all__'

        serializer = OwnerSerializer(allow_null=True)

        instance = serializer.get_object({'id': 999})

        self.assertIsNone(instance)

    def test_get_object_allows_create_when_not_found(self):

        class OwnerSerializer(ModelSerializer):

            class Meta:
                model = Owner
                session = session
                fields = '__all__'

        serializer = OwnerSerializer(allow_create=True)

        instance = serializer.get_object({'id': 999})

        self.assertIsNotNone(instance)
