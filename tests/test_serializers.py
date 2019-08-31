# -*- coding: utf-8 -*-
import copy
from collections import OrderedDict
from decimal import Decimal

from django.core.exceptions import ImproperlyConfigured, ValidationError as DjangoValidationError
from django.test import SimpleTestCase

from django_sorcery.db.meta import model_info

from rest_framework import fields
from rest_framework.exceptions import ErrorDetail, ValidationError
from rest_framework.serializers import ListSerializer, Serializer
from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory

from rest_witchcraft.fields import HyperlinkedIdentityField
from rest_witchcraft.serializers import BaseSerializer, CompositeSerializer, ExpandableModelSerializer, ModelSerializer

from .models import COLORS, Engine, ModelWithJson, Option, Owner, Vehicle, VehicleOther, VehicleType, session


class VehicleOwnerStubSerializer(Serializer):
    id = fields.IntegerField(source="_owner_id")


class VehicleSerializer(ExpandableModelSerializer):
    class Meta(object):
        model = Vehicle
        session = session
        expandable_fields = {"owner": VehicleOwnerStubSerializer(source="*", read_only=True)}
        exclude = ["other"]
        extra_kwargs = {"owner": {"allow_nested_updates": True}}
        nested_serializer_class = ExpandableModelSerializer


class TestModelSerializer(SimpleTestCase):
    def setUp(self):
        super().setUp()
        session.add(Owner(id=1, first_name="Test", last_name="Owner"))
        session.add_all(
            [
                Option(id=1, name="Option 1"),
                Option(id=2, name="Option 2"),
                Option(id=3, name="Option 3"),
                Option(id=4, name="Option 4"),
            ]
        )
        session.flush()
        self.maxDiff = None

    def tearDown(self):
        super().tearDown()
        session.rollback()

    def test_cannot_initialize_without_a_meta(self):
        class VehicleSerializer(ModelSerializer):
            pass

        with self.assertRaises(AttributeError):
            VehicleSerializer()

    def test_cannot_initialize_without_a_session(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                pass

        with self.assertRaises(AssertionError):
            serializer = VehicleSerializer()
            serializer.session

    def test_cannot_initialize_without_a_model_with_session_meta(self):
        class VehicleSerializer(ModelSerializer):
            class Meta(object):
                session = session

        with self.assertRaises(AssertionError):
            serializer = VehicleSerializer()
            serializer.model

    def test_cannot_initialize_without_a_model_with_session_kwarg(self):
        class VehicleSerializer(ModelSerializer):
            class Meta(object):
                pass

        with self.assertRaises(AssertionError):
            serializer = VehicleSerializer(session=session)
            serializer.model

    def test_get_fields_sets_url_field_name_when_missing(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                exclude = ("name",)

        serializer = VehicleSerializer()
        serializer.get_fields()

        self.assertEqual(serializer.url_field_name, api_settings.URL_FIELD_NAME)

    def test_raises_type_error_if_fields_is_not_a_list_or_tuple(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "name"

        serializer = VehicleSerializer()

        with self.assertRaises(TypeError):
            serializer.get_fields()

    def test_raises_type_error_if_exclude_is_not_a_list_or_tuple(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                exclude = "name"

        serializer = VehicleSerializer()

        with self.assertRaises(TypeError):
            serializer.get_fields()

    def test_get_default_field_names_should_get_all_field_names(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("id", "name")

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        field_names = serializer.get_default_field_names({}, info)
        self.assertEqual(
            set(field_names),
            {
                Vehicle.created_at.key,
                Vehicle.engine.key,
                Vehicle.id.key,
                Vehicle.name.key,
                Vehicle.options.key,
                Vehicle.other.key,
                Vehicle.owner.key,
                Vehicle.paint.key,
                Vehicle.type.key,
                Vehicle.is_used.key,
            },
        )

    def test_get_field_names_with_include(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("id", "name")

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        field_names = serializer.get_field_names([], info)
        self.assertEqual(set(field_names), {Vehicle.id.key, Vehicle.name.key})

    def test_get_field_names_with_exclude(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                exclude = ("type", "options")

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        field_names = serializer.get_field_names({}, info)
        self.assertEqual(
            set(field_names),
            {
                Vehicle.created_at.key,
                Vehicle.engine.key,
                Vehicle.id.key,
                Vehicle.name.key,
                Vehicle.other.key,
                Vehicle.owner.key,
                Vehicle.paint.key,
                Vehicle.is_used.key,
            },
        )

    def test_generate_all_fields(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"

        serializer = VehicleSerializer()
        generated_fields = serializer.get_fields()

        self.assertIn(Vehicle.id.key, generated_fields)
        self.assertIn(Vehicle.type.key, generated_fields)
        self.assertIn(Vehicle.name.key, generated_fields)
        self.assertIn(Vehicle.engine.key, generated_fields)
        self.assertIn(Vehicle.owner.key, generated_fields)
        self.assertIn(Vehicle.options.key, generated_fields)

        self.assertFalse(generated_fields[Vehicle.options.key].read_only)

    def test_overwrite_extra_kwargs(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"

        serializer = VehicleSerializer(extra_kwargs={Vehicle.options.key: {"read_only": True}})
        generated_fields = serializer.get_fields()

        self.assertIn(Vehicle.id.key, generated_fields)
        self.assertIn(Vehicle.type.key, generated_fields)
        self.assertIn(Vehicle.name.key, generated_fields)
        self.assertIn(Vehicle.engine.key, generated_fields)
        self.assertIn(Vehicle.owner.key, generated_fields)
        self.assertIn(Vehicle.options.key, generated_fields)

        self.assertTrue(generated_fields[Vehicle.options.key].read_only)

    def test_overwrite_fields_exlude(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"

        serializer = VehicleSerializer(fields=None, exclude=["options"])
        generated_fields = serializer.get_fields()

        self.assertIn(Vehicle.id.key, generated_fields)
        self.assertIn(Vehicle.type.key, generated_fields)
        self.assertIn(Vehicle.name.key, generated_fields)
        self.assertIn(Vehicle.engine.key, generated_fields)
        self.assertIn(Vehicle.owner.key, generated_fields)
        self.assertNotIn(Vehicle.options.key, generated_fields)

    def test_declared_field(self):
        class VehicleSerializer(ModelSerializer):
            name = fields.ChoiceField(choices=["a", "b"])

            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"

        serializer = VehicleSerializer()
        generated_fields = serializer.get_fields()

        self.assertIsInstance(generated_fields["name"], fields.ChoiceField)

    def test_get_field_names_includes_all_required_fields(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("id", "name")

        serializer = VehicleSerializer()
        info = model_info(Vehicle)

        with self.assertRaises(AssertionError):
            serializer.get_field_names(["type"], info)

    def test_include_extra_kwargs(self):

        serializer = BaseSerializer()

        kwargs = {}
        extra_kwargs = {}

        kwargs = serializer.include_extra_kwargs(kwargs, extra_kwargs)

        self.assertEqual(kwargs, {})

    def test_include_extra_kwargs_filter_when_read_only(self):

        serializer = BaseSerializer()

        kwargs = {
            "allow_blank": True,
            "allow_null": True,
            "default": True,
            "max_length": 255,
            "max_value": 255,
            "min_length": 0,
            "min_value": 0,
            "queryset": None,
            "required": True,
            "validators": None,
        }
        extra_kwargs = {"read_only": True}

        kwargs = serializer.include_extra_kwargs(kwargs, extra_kwargs)

        self.assertEqual(kwargs, {"read_only": True})

    def test_include_extra_kwargs_filter_required_when_default_provided(self):

        serializer = BaseSerializer()

        kwargs = {"required": False}
        extra_kwargs = {"default": True}

        kwargs = serializer.include_extra_kwargs(kwargs, extra_kwargs)

        self.assertEqual(kwargs, {"default": True})

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
                fields = ("id", "name")

        serializer = VehicleSerializer()
        extra_kwargs = serializer.get_extra_kwargs()
        self.assertEqual(extra_kwargs, {})

    def test_get_extra_kwargs_with_extra_kwargs(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("id", "name")
                extra_kwargs = {"name": {"read_only": True}}

        serializer = VehicleSerializer()
        extra_kwargs = serializer.get_extra_kwargs()
        self.assertEqual(extra_kwargs, {"name": {"read_only": True}})

    def test_get_extra_kwargs_with_read_only_fields(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("id", "name")
                read_only_fields = ("id", "name")

        serializer = VehicleSerializer()
        extra_kwargs = serializer.get_extra_kwargs()
        self.assertEqual(extra_kwargs, {"id": {"read_only": True}, "name": {"read_only": True}})

    def test_get_extra_kwargs_with_read_only_fields_as_string(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("id", "name")
                read_only_fields = "id"

        with self.assertRaises(TypeError):
            VehicleSerializer()

    def test_build_standard_integer_field(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        field = serializer.build_field(Vehicle.id.key, info, Vehicle, 0)

        self.assertEqual(field.help_text, Vehicle.id.doc)
        self.assertEqual(field.label, "Id")
        self.assertFalse(field.allow_null)
        self.assertIsInstance(field, fields.IntegerField)
        self.assertFalse(field.required)

    def test_build_standard_char_field(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        field = serializer.build_field(Vehicle.name.key, info, Vehicle, 0)

        self.assertEqual(field.help_text, Vehicle.name.doc)
        self.assertEqual(field.label, "Name")
        self.assertFalse(field.required)
        self.assertIsInstance(field, fields.CharField)
        self.assertTrue(field.allow_null)

    def test_build_enum_field(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("type",)

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        field = serializer.build_field(Vehicle.type.key, info, Vehicle, 0)

        self.assertEqual(field.help_text, Vehicle.type.doc)
        self.assertEqual(field.label, "Type")
        self.assertTrue(field.required)
        self.assertIsInstance(field, fields.ChoiceField)
        self.assertFalse(field.allow_null)

    def test_build_choice_field(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("paint",)

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        field = serializer.build_field(Vehicle.paint.key, info, Vehicle, 0)

        self.assertEqual(field.help_text, Vehicle.paint.doc)
        self.assertEqual(field.label, "Paint")
        self.assertFalse(field.required)
        self.assertIsInstance(field, fields.ChoiceField)
        self.assertEqual(field.choices, OrderedDict([(color, color) for color in COLORS]))
        self.assertTrue(field.allow_null)

    def test_fail_when_a_field_type_not_found(self):
        class JSSerializer(ModelSerializer):
            class Meta:
                model = ModelWithJson
                session = session
                fields = ("js",)

        serializer = JSSerializer()
        with self.assertRaises(KeyError) as e:
            serializer.fields

        self.assertEqual(e.exception.args, ("Could not figure out type for attribute 'ModelWithJson.js'",))

    def test_build_url_field(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                exclude = ("name",)

            def get_default_field_names(self, declared_fields, info):
                return super().get_default_field_names(declared_fields, info) + ["url"]

        serializer = VehicleSerializer()
        fields = serializer.get_fields()
        self.assertIn("url", fields)

        url_field = fields.get("url")

        self.assertIsInstance(url_field, HyperlinkedIdentityField)
        self.assertEqual(url_field.view_name, "vehicle-detail")

    def test_build_composite_field(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        field = serializer.build_field(Vehicle.engine.key, info, Vehicle, 0)

        self.assertIsInstance(field, CompositeSerializer)
        self.assertEqual(len(field.fields), 4)

    def test_deepcopy_composite_field(self):
        class EngineSerializer(CompositeSerializer):
            pass

        serializer = EngineSerializer(composite=Vehicle.engine)

        clone = copy.deepcopy(serializer)

        self.assertNotEqual(id(serializer), id(clone))
        self.assertEqual(serializer._args, clone._args)
        self.assertDictEqual(serializer._kwargs, clone._kwargs)

    def test_build_property_field(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        field = serializer.build_field("lower_name", info, Vehicle, 0)

        self.assertIsInstance(field, fields.ReadOnlyField)

    def test_build_unknows_field(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"

        serializer = VehicleSerializer()
        info = model_info(Vehicle)

        with self.assertRaises(ImproperlyConfigured):
            serializer.build_field("abcde", info, Vehicle, 0)

    def test_build_one_to_many_relationship_field(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        nested_serializer = serializer.build_field(Vehicle.owner.key, info, Vehicle, 0)

        self.assertIsNotNone(nested_serializer)
        self.assertIsInstance(nested_serializer, ModelSerializer)
        self.assertEqual(len(nested_serializer.fields), 3)

    def test_build_one_to_many_relationship_field_with_nested_updates_disabled(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"
                extra_kwargs = {"owner": {"allow_nested_updates": False}}

        serializer = VehicleSerializer()
        info = model_info(Vehicle)
        nested_serializer = serializer.build_field(Vehicle.owner.key, info, Vehicle, 0)

        self.assertIsNotNone(nested_serializer)
        self.assertIsInstance(nested_serializer, ModelSerializer)
        self.assertEqual(len(nested_serializer.fields), 3)
        self.assertTrue(nested_serializer.fields["first_name"].read_only)
        self.assertTrue(nested_serializer.fields["last_name"].read_only)

    def test_generated_nested_serializer_get_session_from_parent(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                fields = "__all__"
                depth = 3

        serializer = VehicleSerializer(context={"session": session})

        owner_serializer = serializer.fields["owner"]

        self.assertEqual(owner_serializer.session, session)

    def test_declared_nested_serializer_get_session_from_context(self):
        class OwnerSerializer(ModelSerializer):
            class Meta:
                model = Owner
                fields = "__all__"

        class VehicleSerializer(ModelSerializer):
            Owner = OwnerSerializer()

            class Meta:
                model = Vehicle
                fields = "__all__"

        serializer = VehicleSerializer(context={"session": session})

        owner_serializer = serializer.fields["owner"]

        self.assertEqual(owner_serializer.session, session)

    def test_declared_nested_serializer_get_session_from_root_meta(self):
        class OwnerSerializer(ModelSerializer):
            class Meta:
                model = Owner
                fields = "__all__"

        class VehicleSerializer(ModelSerializer):
            Owner = OwnerSerializer()

            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"

        serializer = VehicleSerializer()

        owner_serializer = serializer.fields["owner"]

        self.assertEqual(owner_serializer.session, session)

    def test_build_serializer_with_depth(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"
                depth = 3

        serializer = VehicleSerializer()

        self.assertEqual(len(serializer.fields), 10)
        self.assertEqual(
            set(serializer.fields.keys()),
            {
                Vehicle.created_at.key,
                Vehicle.engine.key,
                Vehicle.id.key,
                Vehicle.name.key,
                Vehicle.options.key,
                Vehicle.other.key,
                Vehicle.owner.key,
                Vehicle.paint.key,
                Vehicle.type.key,
                Vehicle.is_used.key,
            },
        )

        engine_serializer = serializer.fields["engine"]
        self.assertEqual(len(engine_serializer.fields), 4)
        self.assertEqual(set(engine_serializer.fields.keys()), {"type_", "displacement", "fuel_type", "cylinders"})

        owner_serializer = serializer.fields["owner"]
        self.assertEqual(len(owner_serializer.fields), 3)
        self.assertEqual(set(owner_serializer.fields.keys()), {"id", "first_name", "last_name"})
        self.assertEqual({f.label for f in owner_serializer.fields.values()}, {"Id", "First name", "Last name"})

        options_serializer = serializer.fields["options"]
        self.assertTrue(options_serializer.many)
        self.assertIsInstance(options_serializer, ListSerializer)

        option_serializer = options_serializer.child
        self.assertEqual(len(option_serializer.fields), 2)
        self.assertEqual(set(option_serializer.fields.keys()), {"id", "name"})

    def test_serializer_zero_depth_invalid_error_message(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"

        serializer = VehicleSerializer(data={})

        self.assertFalse(serializer.is_valid())

        self.assertDictEqual(dict(serializer.errors), {"type": ["This field is required."]})

    def test_serializer_zero_depth_post_basic_validation(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"
                extra_kwargs = {"other": {"required": False}}

        data = {
            "name": "Test vehicle",
            "one": "Two",
            "type": "bus",
            "engine": {"displacement": 1234, "cylinders": 4},
            "owner": {"id": 1},
            "options": [],
        }
        serializer = VehicleSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        self.assertDictEqual(
            dict(serializer.validated_data),
            {
                "name": "Test vehicle",
                "type": VehicleType.bus,
                "engine": {"displacement": Decimal("1234.00"), "cylinders": 4},
                "owner": {"id": 1},
                "options": [],
            },
        )

    def test_serializer_create(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"
                extra_kwargs = {"other": {"required": False, "allow_create": False}}

        data = {
            "name": "Test vehicle",
            "one": "Two",
            "type": "bus",
            "engine": {"displacement": 1234, "cylinders": 4},
            "owner": {"id": 1},
            "options": [],
        }

        serializer = VehicleSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.save()

        self.assertEqual(vehicle.name, data["name"])
        self.assertEqual(vehicle.type, VehicleType.bus)
        self.assertEqual(vehicle.engine.cylinders, data["engine"]["cylinders"])
        self.assertEqual(vehicle.engine.displacement, data["engine"]["displacement"])
        self.assertIsNone(vehicle.engine.fuel_type)
        self.assertIsNone(vehicle.engine.type_)
        self.assertEqual(vehicle.owner.id, data["owner"]["id"])
        self.assertEqual(vehicle.owner.first_name, "Test")
        self.assertEqual(vehicle.owner.last_name, "Owner")
        self.assertEqual(vehicle.options, data["options"])

    def test_serializer_create_diff_field_source(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"
                extra_kwargs = {"other": {"required": False, "allow_create": False}}

            def get_fields(self):
                fields = super().get_fields()
                fields["vehicle_type"] = fields.pop("type")
                fields["vehicle_type"].source = "type"
                return fields

        data = {
            "name": "Test vehicle",
            "one": "Two",
            "vehicle_type": "Bus",
            "engine": {"displacement": 1234, "cylinders": 4},
            "owner": {"id": 1},
            "options": [],
        }

        serializer = VehicleSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.save()

        self.assertEqual(vehicle.name, data["name"])
        self.assertEqual(vehicle.type, VehicleType(data["vehicle_type"]))
        self.assertEqual(vehicle.engine.cylinders, data["engine"]["cylinders"])
        self.assertEqual(vehicle.engine.displacement, data["engine"]["displacement"])
        self.assertIsNone(vehicle.engine.fuel_type)
        self.assertIsNone(vehicle.engine.type_)
        self.assertEqual(vehicle.owner.id, data["owner"]["id"])
        self.assertEqual(vehicle.owner.first_name, "Test")
        self.assertEqual(vehicle.owner.last_name, "Owner")
        self.assertEqual(vehicle.options, data["options"])

    def test_serializer_create_model_validations(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"
                extra_kwargs = {"other": {"required": False, "allow_create": False}}

        data = {
            "name": "invalid",
            "one": "Two",
            "type": "Bus",
            "engine": {"displacement": 1234, "cylinders": 4},
            "owner": {"id": 1},
            "options": [],
        }

        serializer = VehicleSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        with self.assertRaises(ValidationError) as e:
            serializer.save()

        self.assertDictEqual(e.exception.detail, {"name": ["invalid vehicle name"]})

    def test_serializer_create_star_source(self):
        class BasicSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ["name", "type"]

        class VehicleSerializer(ModelSerializer):
            basic = BasicSerializer(source="*", allow_nested_updates=True)

            class Meta:
                model = Vehicle
                session = session
                exclude = ["name", "type"]
                extra_kwargs = {"other": {"required": False, "allow_create": False}}

        data = {
            "basic": {"name": "Test vehicle", "type": "Bus"},
            "one": "Two",
            "engine": {"displacement": 1234, "cylinders": 4},
            "owner": {"id": 1},
            "options": [],
        }

        serializer = VehicleSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.save()

        self.assertEqual(vehicle.name, data["basic"]["name"])
        self.assertEqual(vehicle.type, VehicleType(data["basic"]["type"]))
        self.assertEqual(vehicle.engine.cylinders, data["engine"]["cylinders"])
        self.assertEqual(vehicle.engine.displacement, data["engine"]["displacement"])
        self.assertIsNone(vehicle.engine.fuel_type)
        self.assertIsNone(vehicle.engine.type_)
        self.assertEqual(vehicle.owner.id, data["owner"]["id"])
        self.assertEqual(vehicle.owner.first_name, "Test")
        self.assertEqual(vehicle.owner.last_name, "Owner")
        self.assertEqual(vehicle.options, data["options"])

    def test_post_update(self):

        vehicle = Vehicle(
            name="Test vehicle",
            type=VehicleType.bus,
            engine=Engine(4, 1234, None, None),
            owner=session.query(Owner).get(1),
        )

        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"
                extra_kwargs = {"other": {"required": False, "allow_create": True, "allow_nested_updates": True}}

        data = {
            "name": "Another test vechicle",
            "one": "Two",
            "type": "Car",
            "engine": {"displacement": 4321, "cylinders": 2, "type_": "banana", "fuel_type": "petrol"},
            "owner": {"id": 1},
            "options": [],
            "other": {"advertising_cost": 4321},
        }

        serializer = VehicleSerializer(instance=vehicle, data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.save()

        self.assertEqual(vehicle.name, data["name"])
        self.assertEqual(vehicle.type, VehicleType(data["type"]))
        self.assertEqual(vehicle.engine.cylinders, data["engine"]["cylinders"])
        self.assertEqual(vehicle.engine.displacement, data["engine"]["displacement"])
        self.assertEqual(vehicle.engine.fuel_type, data["engine"]["fuel_type"])
        self.assertEqual(vehicle.engine.type_, data["engine"]["type_"])
        self.assertEqual(vehicle.owner.id, data["owner"]["id"])
        self.assertEqual(vehicle.owner.first_name, "Test")
        self.assertEqual(vehicle.owner.last_name, "Owner")
        self.assertEqual(vehicle.options, data["options"])
        self.assertEqual(vehicle.other.advertising_cost, 4321)

    def test_post_update_remove_composite(self):
        vehicle = Vehicle(
            name="Test vehicle",
            type=VehicleType.bus,
            engine=Engine(4, 1234, None, None),
            owner=session.query(Owner).get(1),
        )

        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"
                extra_kwargs = {
                    "other": {"required": False, "allow_create": True, "allow_nested_updates": True},
                    "engine": {"required": False, "allow_null": True},
                }

        data = {
            "name": "Another test vechicle",
            "one": "Two",
            "type": "Car",
            "engine": None,
            "owner": {"id": 1},
            "options": [],
            "other": {"advertising_cost": 4321},
        }

        serializer = VehicleSerializer(instance=vehicle, data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.save()

        self.assertEqual(vehicle.name, data["name"])
        self.assertEqual(vehicle.type, VehicleType(data["type"]))
        self.assertEqual(vehicle.owner.id, data["owner"]["id"])
        self.assertEqual(vehicle.owner.first_name, "Test")
        self.assertEqual(vehicle.owner.last_name, "Owner")
        self.assertEqual(vehicle.options, data["options"])
        self.assertEqual(vehicle.other.advertising_cost, 4321)
        self.assertIsNone(vehicle.engine.cylinders)
        self.assertIsNone(vehicle.engine.displacement)
        self.assertIsNone(vehicle.engine.fuel_type)
        self.assertIsNone(vehicle.engine.type_)

    def test_patch_update(self):

        vehicle = Vehicle(
            name="Test vehicle",
            type=VehicleType.bus,
            engine=Engine(4, 1234, None, None),
            owner=session.query(Owner).get(1),
            other=VehicleOther(advertising_cost=4321),
        )

        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"
                extra_kwargs = {"other": {"required": False, "allow_create": True, "allow_nested_updates": True}}

        data = {"other": {"advertising_cost": 1234}}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.save()

        self.assertEqual(vehicle.other.advertising_cost, data["other"]["advertising_cost"])

    def test_patch_update_with_nested_id(self):

        vehicle = Vehicle(
            name="Test vehicle",
            type=VehicleType.bus,
            engine=Engine(4, 1234, None, None),
            owner=session.query(Owner).get(1),
            other=VehicleOther(advertising_cost=4321),
        )
        session.add(vehicle)
        session.flush()

        other = vehicle.other

        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("other",)
                extra_kwargs = {"other": {"allow_nested_updates": True}}

        data = {"other": {"id": vehicle.other.id, "advertising_cost": 1234}}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.save()

        self.assertEqual(vehicle.other.advertising_cost, data["other"]["advertising_cost"])
        self.assertEqual(vehicle.other, other)

    def test_patch_update_nested_set_null(self):

        vehicle = Vehicle(
            name="Test vehicle",
            type=VehicleType.bus,
            engine=Engine(4, 1234, None, None),
            owner=session.query(Owner).get(1),
            other=VehicleOther(advertising_cost=4321),
        )

        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("other",)
                extra_kwargs = {"other": {"allow_create": True, "allow_null": True}}

        data = {"other": None}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.save()

        self.assertIsNone(vehicle.other)

    def test_patch_update_nested_set_null_allow_null_false(self):

        vehicle = Vehicle(
            name="Test vehicle",
            type=VehicleType.bus,
            engine=Engine(4, 1234, None, None),
            owner=session.query(Owner).get(1),
            other=VehicleOther(advertising_cost=4321),
        )

        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("other",)
                extra_kwargs = {"other": {"allow_create": True, "allow_null": False}}

        data = {"other": None}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)

        self.assertFalse(serializer.is_valid(), serializer.errors)

    def test_patch_update_nested_set_null_allow_create_false(self):

        vehicle = Vehicle(
            name="Test vehicle",
            type=VehicleType.bus,
            engine=Engine(4, 1234, None, None),
            owner=session.query(Owner).get(1),
            other=VehicleOther(advertising_cost=4321),
        )

        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("other",)
                extra_kwargs = {"other": {"allow_create": False, "allow_null": True}}

        data = {"other": None}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.save()

        self.assertIsNone(vehicle.other)

    def test_composite_serializer_can_create(self):
        class EngineSerializer(CompositeSerializer):
            class Meta:
                composite = Vehicle.engine

        data = {"cylinders": 2, "displacement": 1234, "fuel_type": "petrol", "type_": "banana"}

        serializer = EngineSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        engine = serializer.save()

        self.assertIsInstance(engine, Engine)
        self.assertEqual(engine.cylinders, 2)
        self.assertEqual(engine.displacement, 1234)
        self.assertEqual(engine.fuel_type, "petrol")
        self.assertEqual(engine.type_, "banana")

    def test_composite_serializer_can_update(self):
        class EngineSerializer(CompositeSerializer):
            class Meta:
                composite = Vehicle.engine

        data = {"cylinders": 2, "displacement": 1234, "fuel_type": "diesel", "type_": "banana"}
        engine = Engine(4, 2345, "apple", "petrol")

        serializer = EngineSerializer(engine, data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        engine = serializer.save()

        self.assertIsInstance(engine, Engine)
        self.assertEqual(engine.cylinders, 2)
        self.assertEqual(engine.displacement, 1234)
        self.assertEqual(engine.fuel_type, "diesel")
        self.assertEqual(engine.type_, "banana")

    def test_composite_serializer_can_update_patch(self):
        class EngineSerializer(CompositeSerializer):
            class Meta:
                composite = Vehicle.engine

        data = {"cylinders": 2}
        engine = Engine(4, 2345, "apple", "petrol")

        serializer = EngineSerializer(engine, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        engine = serializer.save()

        self.assertIsInstance(engine, Engine)
        self.assertEqual(engine.cylinders, 2)
        self.assertEqual(engine.displacement, 2345)
        self.assertEqual(engine.fuel_type, "petrol")
        self.assertEqual(engine.type_, "apple")

    def test_composite_serializer_can_use_custom_setter(self):
        class EngineSerializer(CompositeSerializer):
            class Meta:
                composite = Vehicle.engine

            def set_cylinders(self, instance, field, value):
                self.called = True
                instance.cylinders = value

        data = {"cylinders": 2}
        engine = Engine(4, 2345, "apple", "petrol")

        serializer = EngineSerializer(engine, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        serializer.save()

        self.assertTrue(serializer.called)

    def test_composite_serializer_can_handle_errors_during_update(self):
        class EngineSerializer(CompositeSerializer):
            class Meta:
                composite = Vehicle.engine

            def set_cylinders(self, instance, field, value):
                raise AssertionError("Some error")

        data = {"cylinders": 2}
        engine = Engine(4, 2345, "apple", "petrol")

        serializer = EngineSerializer(engine, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        with self.assertRaises(ValidationError):
            serializer.save()

    def test_patch_update_to_list_with_empty_list_clears_it(self):
        vehicle = Vehicle(
            name="Test vehicle",
            type=VehicleType.bus,
            engine=Engine(4, 1234, None, None),
            owner=session.query(Owner).get(1),
            other=VehicleOther(advertising_cost=4321),
            options=session.query(Option).all(),
        )

        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("options",)

        data = {"options": []}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.save()

        self.assertEqual(len(vehicle.options), 0)

    def test_patch_update_to_list_with_new_list(self):
        vehicle = Vehicle(
            name="Test vehicle",
            type=VehicleType.bus,
            engine=Engine(4, 1234, None, None),
            owner=session.query(Owner).get(1),
            other=VehicleOther(advertising_cost=4321),
            options=session.query(Option).filter(Option.id.in_([1, 2])).all(),
        )

        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("options",)

        data = {"options": [{"id": 3}, {"id": 4}]}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.update(vehicle, serializer.validated_data)

        self.assertEqual(len(vehicle.options), 2)
        self.assertEqual({v.id for v in vehicle.options}, {3, 4})

    def test_patch_update_to_list_with_new_list_with_allow_create(self):
        vehicle = Vehicle(
            name="Test vehicle",
            type=VehicleType.bus,
            engine=Engine(4, 1234, None, None),
            owner=session.query(Owner).get(1),
            other=VehicleOther(advertising_cost=4321),
            options=session.query(Option).filter(Option.id.in_([1, 2])).all(),
        )

        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("options",)
                extra_kwargs = {"options": {"allow_create": True}}

        data = {"options": [{"name": "Test"}, {"name": "Other Test"}]}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.update(vehicle, serializer.validated_data)

        self.assertEqual(len(vehicle.options), 2)
        self.assertEqual({v.name for v in vehicle.options}, {"Test", "Other Test"})

    def test_patch_update_to_list_with_new_list_with_nested(self):
        vehicle = Vehicle(
            name="Test vehicle",
            type=VehicleType.bus,
            engine=Engine(4, 1234, None, None),
            owner=session.query(Owner).get(1),
            other=VehicleOther(advertising_cost=4321),
            options=session.query(Option).filter(Option.id.in_([1, 2])).all(),
        )

        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("options",)
                extra_kwargs = {"options": {"allow_nested_updates": True}}

        data = {"options": [{"id": 1, "name": "Test 1"}, {"id": 2, "name": "Test 2"}]}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        vehicle = serializer.update(vehicle, serializer.validated_data)

        self.assertEqual([option.id for option in vehicle.options], [1, 2])
        self.assertEqual([option.name for option in vehicle.options], ["Test 1", "Test 2"])

    def test_patch_update_to_list_with_new_list_with_nested_raises_for_a_bad_pk(self):
        vehicle = Vehicle(
            name="Test vehicle",
            type=VehicleType.bus,
            engine=Engine(4, 1234, None, None),
            owner=session.query(Owner).get(1),
            other=VehicleOther(advertising_cost=4321),
            options=session.query(Option).filter(Option.id.in_([1, 2])).all(),
        )

        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("options",)
                extra_kwargs = {"options": {"allow_null": False}}

        data = {"options": [{"id": 1, "name": "Test 1"}, {"id": 5, "name": "Test 5"}]}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        with self.assertRaises(ValidationError):
            serializer.update(vehicle, serializer.validated_data)

    def test_update_generates_validation_error_when_required_many_to_one_instance_not_found(self):
        vehicle = Vehicle(
            name="Test vehicle",
            type=VehicleType.bus,
            engine=Engine(4, 1234, None, None),
            owner=session.query(Owner).get(1),
            other=VehicleOther(advertising_cost=4321),
            options=session.query(Option).filter(Option.id.in_([1, 2])).all(),
        )

        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("owner",)
                extra_kwargs = {"owner": {"allow_null": False}}

        data = {"owner": {"id": 1234}}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        with self.assertRaises(ValidationError):
            serializer.update(vehicle, serializer.validated_data)

    def test_update_calls_custom_setter(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("name",)

            def set_name(self, instance, field, value):
                self._set_name_called = True

        vehicle = Vehicle(
            name="Test vehicle",
            type=VehicleType.bus,
            engine=Engine(4, 1234, None, None),
            owner=session.query(Owner).get(1),
            other=VehicleOther(advertising_cost=4321),
            options=session.query(Option).filter(Option.id.in_([1, 2])).all(),
        )

        data = {"name": "Bob Loblaw"}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        serializer.update(vehicle, serializer.validated_data)
        self.assertTrue(serializer._set_name_called)

    def test_update_calls_custom_setter_django_validation_error(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = ("name",)

            def set_name(self, instance, field, value):
                raise DjangoValidationError({"name": [DjangoValidationError("error here")]})

        vehicle = Vehicle(name="Test vehicle")

        data = {"name": "Bob Loblaw"}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        with self.assertRaises(ValidationError) as e:
            serializer.update(vehicle, serializer.validated_data)

        self.assertEqual(e.exception.detail, {"name": ["error here"]})

    def test_update_composite_calls_custom_setter_django_validation_error(self):
        class EngineSerializer(CompositeSerializer):
            class Meta:
                composite = Vehicle.engine

            def set_cylinders(self, instance, field, value):
                raise DjangoValidationError({"cylinders": [DjangoValidationError("error here")]})

        class VehicleSerializer(ModelSerializer):
            engine = EngineSerializer()

            class Meta:
                model = Vehicle
                session = session
                fields = ("engine",)

            def set_name(self, instance, field, value):
                raise DjangoValidationError({"name": [DjangoValidationError("error here")]})

        vehicle = Vehicle()

        data = {"engine": {"cylinders": 10}}

        serializer = VehicleSerializer(instance=vehicle, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        with self.assertRaises(ValidationError) as e:
            serializer.update(vehicle, serializer.validated_data)

        self.assertEqual(e.exception.detail, {"engine": {"cylinders": [ErrorDetail("error here", code="invalid")]}})

    def test_get_object_can_get_object(self):
        class OwnerSerializer(ModelSerializer):
            class Meta:
                model = Owner
                session = session
                fields = "__all__"

        serializer = OwnerSerializer()
        instance = serializer.get_object({"id": 1})

        self.assertIsNotNone(instance)
        self.assertIsInstance(instance, Owner)

    def test_get_object_raise_when_not_found(self):
        class OwnerSerializer(ModelSerializer):
            class Meta:
                model = Owner
                session = session
                fields = "__all__"

        serializer = OwnerSerializer()

        with self.assertRaises(ValidationError):
            serializer.get_object({"id": 999})

    def test_get_object_existing_instance(self):
        class OwnerSerializer(ModelSerializer):
            class Meta:
                model = Owner
                session = session
                fields = "__all__"

        existing = Owner()
        serializer = OwnerSerializer(allow_null=True)
        instance = serializer.get_object({}, existing)

        self.assertIsNotNone(instance)
        self.assertIs(instance, existing)

    def test_get_object_allow_null(self):
        class OwnerSerializer(ModelSerializer):
            class Meta:
                model = Owner
                session = session
                fields = "__all__"

        serializer = OwnerSerializer(allow_null=True)

        self.assertIsNone(serializer.get_object(None, Owner()))

    def test_get_object_allows_create(self):
        class OwnerSerializer(ModelSerializer):
            class Meta:
                model = Owner
                session = session
                fields = "__all__"

        serializer = OwnerSerializer(allow_create=True)
        instance = serializer.get_object({})

        self.assertIsNotNone(instance)
        self.assertIsInstance(instance, Owner)

    def test_get_object_no_object(self):
        class OwnerSerializer(ModelSerializer):
            class Meta:
                model = Owner
                session = session
                fields = "__all__"

        serializer = OwnerSerializer()

        with self.assertRaises(ValidationError):
            serializer.get_object({})

    def test_to_internal_value_partial_by_pk(self):
        class OwnerSerializer(ModelSerializer):
            class Meta:
                model = Owner
                session = session
                fields = "__all__"

        serializer = OwnerSerializer(data={"id": 1}, partial_by_pk=True)

        self.assertTrue(serializer.fields["id"].required)
        self.assertTrue(serializer.is_valid())
        self.assertTrue(serializer.fields["id"].required)
        self.assertFalse(serializer.fields["first_name"].required)
        self.assertFalse(serializer.fields["last_name"].required)

    def test_to_internal_value_partial_by_pk_remove_extra_fields(self):
        class VehicleSerializer(ModelSerializer):
            class Meta:
                model = Vehicle
                session = session
                fields = "__all__"

        class OwnerSerializer(ModelSerializer):
            vehicle = VehicleSerializer(partial_by_pk=True)

            class Meta:
                model = Option
                session = session
                fields = "__all__"

        serializer = OwnerSerializer(data={"id": 111, "name": "foo", "vehicle": {"id": 1}})

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["vehicle"], {"id": 1})

        serializer = OwnerSerializer(data={"id": 111, "name": "foo", "vehicle": {}})
        self.assertFalse(serializer.is_valid(), serializer.errors)

        serializer = OwnerSerializer(data={"id": 111, "name": "foo"})
        self.assertFalse(serializer.is_valid(), serializer.errors)


class TestExpandableModelSerializer(SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.vehicle = Vehicle(
            name="Test vehicle",
            type=VehicleType.bus,
            engine=Engine(4, 1234, None, None),
            owner=Owner(first_name="Jon", last_name="Snow"),
            other=VehicleOther(advertising_cost=4321),
            options=[Option(name="GPS")],
        )
        self.rf = APIRequestFactory()
        self.maxDiff = None

    def test_to_representation_collapsed(self):
        s = VehicleSerializer(instance=self.vehicle)

        self.assertEqual(
            s.data,
            {
                "id": None,
                "name": "Test vehicle",
                "type": "bus",
                "created_at": None,
                "paint": None,
                "is_used": None,
                "engine": {"cylinders": 4, "displacement": "1234.00", "type_": None, "fuel_type": None},
                "owner": {"id": None},
                "options": [{"name": "GPS", "id": None}],
            },
        )

    def test_to_representation_list_collapsed(self):
        s = VehicleSerializer(instance=[self.vehicle], many=True)

        self.assertEqual(
            s.data,
            [
                {
                    "id": None,
                    "name": "Test vehicle",
                    "type": "bus",
                    "created_at": None,
                    "paint": None,
                    "is_used": None,
                    "engine": {"cylinders": 4, "displacement": "1234.00", "type_": None, "fuel_type": None},
                    "owner": {"id": None},
                    "options": [{"name": "GPS", "id": None}],
                }
            ],
        )

    def test_to_representation_request_expanded(self):
        s = VehicleSerializer(instance=self.vehicle, context={"request": self.rf.get("/", {"expand": "owner"})})

        self.assertEqual(
            s.data,
            {
                "id": None,
                "name": "Test vehicle",
                "type": "bus",
                "created_at": None,
                "paint": None,
                "is_used": None,
                "engine": {"cylinders": 4, "displacement": "1234.00", "type_": None, "fuel_type": None},
                "owner": {"id": None, "last_name": "Snow", "first_name": "Jon"},
                "options": [{"name": "GPS", "id": None}],
            },
        )

    def test_to_representation_update_expanded(self):
        s = VehicleSerializer(
            instance=self.vehicle,
            partial=True,
            data={"owner": {"first_name": "John", "last_name": "Doe"}},
            allow_nested_updates=True,
        )

        self.assertTrue(s.is_valid())
        s.save()

        self.assertEqual(
            s.data,
            {
                "id": None,
                "name": "Test vehicle",
                "type": "bus",
                "created_at": None,
                "paint": None,
                "is_used": None,
                "engine": {"cylinders": 4, "displacement": "1234.00", "type_": None, "fuel_type": None},
                "owner": {"id": None, "last_name": "Doe", "first_name": "John"},
                "options": [{"name": "GPS", "id": None}],
            },
        )

    def test_query_serializer(self):
        s = VehicleSerializer().get_query_serializer_class()()

        self.assertEqual(list(s.fields), ["expand"])
        self.assertIsInstance(s.fields["expand"], fields.ListField)
        self.assertIsInstance(s.fields["expand"].child, fields.ChoiceField)
        self.assertEqual(list(s.fields["expand"].child.choices), ["owner"])

    def test_query_serializer_exclude(self):
        s = VehicleSerializer().get_query_serializer_class(exclude=["owner"])()

        self.assertEqual(list(s.fields), [])

    def test_query_serializer_disallow(self):
        s = VehicleSerializer().get_query_serializer_class(disallow=["owner"])()

        self.assertEqual(list(s.fields), ["expand"])
        self.assertIsInstance(s.fields["expand"], fields.ListField)
        self.assertIsInstance(s.fields["expand"].child, fields.ChoiceField)
        self.assertEqual(list(s.fields["expand"].child.choices), [])

    def test_query_serializer_nested(self):
        class Serializer(ExpandableModelSerializer):
            vehicles = VehicleSerializer(many=True)

            class Meta(object):
                model = Owner
                session = session
                fields = "__all__"

        s = Serializer().get_query_serializer_class()()

        self.assertEqual(list(s.fields), ["expand"])
        self.assertIsInstance(s.fields["expand"], fields.ListField)
        self.assertIsInstance(s.fields["expand"].child, fields.ChoiceField)
        self.assertEqual(set(s.fields["expand"].child.choices), {"vehicles__owner"})
