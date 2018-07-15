# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import copy
import re
from collections import OrderedDict

import six
from rest_framework import fields
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ListSerializer, Serializer
from rest_framework.settings import api_settings

from sqlalchemy.orm.interfaces import ONETOMANY

from django.core.exceptions import ImproperlyConfigured, ValidationError as DjangoValidationError
from django.utils.text import capfirst

from django_sorcery.db.meta import composite_info, model_info
from django_sorcery.db.models import get_primary_keys

from .field_mapping import get_field_type, get_url_kwargs
from .fields import UriField
from .utils import django_to_drf_validation_error


ALL_FIELDS = "__all__"
REGEX_TYPE = type(re.compile(""))


class BaseSerializer(Serializer):

    serializer_choice_field = fields.ChoiceField

    @property
    def is_nested(self):
        if self.parent:
            if not hasattr(self.parent, "many"):
                return True

            if self.parent.many is True and self.parent.parent:
                return True

        return False

    def build_standard_field_kwargs(self, field_name, field_class, column_info):
        """
        Analyze model column to generate field kwargs.
        """
        field_kwargs = column_info.field_kwargs
        field_kwargs["label"] = capfirst(" ".join(field_name.split("_")).strip())
        field_kwargs["allow_null"] = not field_kwargs.get("required", True)

        # Include any kwargs defined in `Meta.extra_kwargs`
        field_kwargs = self.include_extra_kwargs(field_kwargs, self._extra_kwargs.get(field_name))

        if "choices" in field_kwargs:
            # Fields with choices get coerced into `ChoiceField`
            # instead of using their regular typed field.
            field_class = self.serializer_choice_field
            # Some model fields may introduce kwargs that would not be valid
            # for the choice field. We need to strip these out.
            # Eg. models.DecimalField(max_digits=3, decimal_places=1, choices=DECIMAL_CHOICES)
            valid_kwargs = {
                "read_only",
                "write_only",
                "required",
                "default",
                "initial",
                "source",
                "label",
                "help_text",
                "style",
                "error_messages",
                "validators",
                "allow_null",
                "allow_blank",
                "choices",
            }
            for key in list(field_kwargs.keys()):
                if key not in valid_kwargs:
                    field_kwargs.pop(key)

        if not issubclass(field_class, fields.CharField) and not issubclass(field_class, fields.ChoiceField):
            # `allow_blank` is only valid for textual fields.
            field_kwargs.pop("allow_blank", None)

        if issubclass(field_class, (fields.NullBooleanField, fields.BooleanField)):
            # 'allow_null' and 'max_length' is not valid kwarg for NullBooleanField
            for kw in {"allow_null", "max_length"}:
                field_kwargs.pop(kw, None)

        return field_kwargs

    def build_standard_field(self, field_name, column_info):
        """
        Create regular model fields.
        """
        field_class = self.get_field_type(column_info)

        field_kwargs = self.build_standard_field_kwargs(field_name, field_class, column_info)

        return field_class(**field_kwargs)

    def get_field_type(self, column_info):
        """
        Returns the field type to be used determined by the sqlalchemy column type or the column type's python type
        """
        field_class = get_field_type(column_info.column)

        if not field_class:
            raise KeyError(
                "Could not figure out type for attribute '{}.{}'".format(self.model.__name__, column_info.property.key)
            )

        return field_class

    def include_extra_kwargs(self, kwargs, extra_kwargs=None):
        """
        Include any 'extra_kwargs' that have been included for this field,
        possibly removing any incompatible existing keyword arguments.
        """
        extra_kwargs = extra_kwargs or {}
        if extra_kwargs.get("read_only", False):
            for attr in [
                "required",
                "default",
                "allow_blank",
                "allow_null",
                "min_length",
                "max_length",
                "min_value",
                "max_value",
                "validators",
                "queryset",
            ]:
                kwargs.pop(attr, None)

        if extra_kwargs.get("default") and kwargs.get("required") is False:
            kwargs.pop("required")

        if extra_kwargs.get("read_only", kwargs.get("read_only", False)):
            # Read only fields should always omit the 'required' argument.
            extra_kwargs.pop("required", None)

        kwargs.update(extra_kwargs)

        return kwargs

    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()

    def update_attribute(self, instance, field, value):
        """
        Performs update on the instance for the given field with value
        """
        field_setter = getattr(self, "set_" + field.field_name, None)
        if field_setter:
            field_setter(instance, field.source, value)
        else:
            setattr(instance, field.source, value)


class CompositeSerializer(BaseSerializer):
    """
    This class is useful for generating a serializer for sqlalchemy's `composite` model attributes.
    """

    def __init__(self, *args, **kwargs):
        composite_attr = kwargs.pop("composite", None) or getattr(getattr(self, "Meta", None), "composite", None)
        self._info = composite_info(composite_attr)
        self.source = kwargs.pop("source", None)

        super(CompositeSerializer, self).__init__(*args, **kwargs)
        self.composite_class = self._info.prop.composite_class
        self.read_only = False
        self.required = False
        self.default = None
        self.allow_nested_updates = True
        self._extra_kwargs = {}

    def get_fields(self):
        """
        Return the dict of field names -> field instances that should be
        used for `self.fields` when instantiating the serializer.
        """
        _fields = OrderedDict()

        for field_name, column_info in self._info.properties.items():
            source = self._extra_kwargs.get(field_name, {}).get("source") or field_name

            _fields[field_name] = self.build_standard_field(source, column_info)

        return _fields

    def get_object(self, validated_data, instance=None):
        if instance:
            return instance

        validated_data = validated_data or {}

        composite_args = [validated_data.get(i) for i in self._info.properties]
        return self.composite_class(*composite_args)

    def create(self, validated_data):
        instance = self.get_object(validated_data)
        return self.update(instance, validated_data)

    def update(self, instance, validated_data):
        errors = {}
        instance = self.perform_update(instance, validated_data, errors)

        if errors:
            raise ValidationError(errors)

        return instance

    def perform_update(self, instance, validated_data, errors):

        validated_data = validated_data or {}

        for field in self._writable_fields:

            if field.field_name not in validated_data:
                continue

            try:
                value = validated_data.get(field.field_name)

                self.update_attribute(instance, field, value)

            except Exception as e:
                errors.setdefault(field.field_name, []).append(" ".join(e.args))

        return instance

    def __deepcopy__(self, memo=None):
        """
        When cloning fields we instantiate using the arguments it was
        originally created with, rather than copying the complete state.
        """
        # Treat regexes, validators and session as immutable.
        args = [copy.deepcopy(item) if not isinstance(item, REGEX_TYPE) else item for item in self._args]
        kwargs = {
            key: (copy.deepcopy(value) if (key not in ("validators", "regex", "composite")) else value)
            for key, value in self._kwargs.items()
        }
        return self.__class__(*args, **kwargs)


class ModelSerializer(BaseSerializer):
    """
    ModelSerializer is basically like a drf model serializer except that it works with
    sqlalchemy models:

    * A set of default fields are automatically populated by introspecting a sqlalchemy model
    * Default `.create()` and `.update()` implementations provided by mostly reducing the problem
      to update.

    The process of automatically determining a set of serializer fields is based on the model's fields, components
    and relationships.

    If the `ModelSerializer` does not generate the set of fields that you need, you can explicitly declare them.
    """

    url_field_name = None
    serializer_url_field = UriField

    def __init__(self, *args, **kwargs):
        """
        ModelSerializer initializer
        The main things that we're interested in is the sqlalchemy session, you can provide it thru `Meta.session`,
        `session` kwarg or thru `context`

        `allow_nested_updates` is for controlling nested related model updates.
        """
        self._session = kwargs.pop("session", None) or getattr(getattr(self, "Meta", None), "session", None)
        self.allow_nested_updates = kwargs.pop("allow_nested_updates", False)
        self.allow_create = kwargs.pop("allow_create", False)

        super(ModelSerializer, self).__init__(*args, **kwargs)

        self._extra_kwargs = self.get_extra_kwargs()

    def __deepcopy__(self, memo=None):
        """
        When cloning fields we instantiate using the arguments it was
        originally created with, rather than copying the complete state.
        """
        # Treat regexes, validators and session as immutable.
        args = [copy.deepcopy(item) if not isinstance(item, REGEX_TYPE) else item for item in self._args]
        kwargs = {
            key: (copy.deepcopy(value) if (key not in ("validators", "regex", "session")) else value)
            for key, value in self._kwargs.items()
        }
        return self.__class__(*args, **kwargs)

    @property
    def session(self):
        if not self._session:

            self._session = self.context.get("session")

        assert self._session is not None, (
            "Creating a ModelSerializer without the session attribute in Meta, as a keyword argument or without"
            "a session in the serializer context"
        )

        return self._session

    @property
    def model(self):
        assert hasattr(self.Meta, "model"), 'Class {serializer_class} missing "Meta.model" attribute'.format(
            serializer_class=self.__class__.__name__
        )
        return self.Meta.model

    def get_fields(self):
        """
        Return the dict of field names -> field instances that should be
        used for `self.fields` when instantiating the serializer.
        """
        if self.url_field_name is None:
            self.url_field_name = api_settings.URL_FIELD_NAME

        assert hasattr(self, "Meta"), 'Class {serializer_class} missing "Meta" attribute'.format(
            serializer_class=self.__class__.__name__
        )

        declared_fields = copy.deepcopy(self._declared_fields)
        info = model_info(getattr(self.Meta, "model"))
        depth = getattr(self.Meta, "depth", 0)

        if depth is not None:
            assert depth >= 0, "'depth' may not be negative."
            assert depth <= 5, "'depth' may not be greater than 5."

        field_names = self.get_field_names(declared_fields, info)

        # Determine the fields that should be included on the serializer.
        _fields = OrderedDict()

        for field_name in field_names:
            # If the field is explicitly declared on the class then use that.
            if field_name in declared_fields:
                _fields[field_name] = declared_fields[field_name]
                continue

            source = self._extra_kwargs.get(field_name, {}).get("source") or field_name

            _fields[field_name] = self.build_field(source, info, self.model, depth)

        return _fields

    def get_field_names(self, declared_fields, info):
        """
        Returns the list of all field names that should be created when
        instantiating this serializer class. This is based on the default
        set of fields, but also takes into account the `Meta.fields` or
        `Meta.exclude` options if they have been specified.
        """
        _fields = getattr(self.Meta, "fields", None)
        exclude = getattr(self.Meta, "exclude", None)

        if _fields and _fields != ALL_FIELDS and not isinstance(_fields, (list, tuple)):
            raise TypeError(
                'The `fields` option must be a list or tuple or "__all__". ' "Got %s." % type(_fields).__name__
            )

        if exclude and not isinstance(exclude, (list, tuple)):
            raise TypeError("The `exclude` option must be a list or tuple. Got %s." % type(exclude).__name__)

        assert not (_fields and exclude), (
            "Cannot set both 'fields' and 'exclude' options on "
            "serializer {serializer_class}.".format(serializer_class=self.__class__.__name__)
        )

        assert not (_fields is None and exclude is None), (
            "Creating a ModelSerializer without either the 'fields' attribute "
            "or the 'exclude' attribute has been deprecated since 3.3.0, "
            "and is now disallowed. Add an explicit fields = '__all__' to the "
            "{serializer_class} serializer.".format(serializer_class=self.__class__.__name__),
        )

        if _fields == ALL_FIELDS:
            _fields = None

        if _fields is not None:
            # Ensure that all declared fields have also been included in the
            # `Meta.fields` option.

            # Do not require any fields that are declared a parent class,
            # in order to allow serializer subclasses to only include
            # a subset of fields.
            required_field_names = set(declared_fields)
            for cls in self.__class__.__bases__:
                required_field_names -= set(getattr(cls, "_declared_fields", []))

            for field_name in required_field_names:
                assert field_name in _fields, (
                    "The field '{field_name}' was declared on serializer "
                    "{serializer_class}, but has not been included in the "
                    "'fields' option.".format(field_name=field_name, serializer_class=self.__class__.__name__)
                )
            return _fields

        # Use the default set of field names if `Meta.fields` is not specified.
        _fields = self.get_default_field_names(declared_fields, info)

        if exclude is not None:
            # If `Meta.exclude` is included, then remove those fields.
            for field_name in exclude:
                assert field_name in _fields, (
                    "The field '{field_name}' was included on serializer "
                    "{serializer_class} in the 'exclude' option, but does "
                    "not match any model field.".format(field_name=field_name, serializer_class=self.__class__.__name__)
                )
                _fields.remove(field_name)

        return _fields

    def get_default_field_names(self, declared_fields, info):
        """
        Return the default list of field names that will be used if the `Meta.fields` option is not specified.
        """
        return info.field_names + [self.url_field_name or api_settings.URL_FIELD_NAME] + list(declared_fields.keys())

    def get_extra_kwargs(self):
        """
        Return a dictionary mapping field names to a dictionary of additional keyword arguments.
        """
        extra_kwargs = copy.deepcopy(getattr(self.Meta, "extra_kwargs", {})) or {}

        read_only_fields = getattr(self.Meta, "read_only_fields", None)
        if read_only_fields is not None:
            if not isinstance(read_only_fields, (list, tuple)):
                raise TypeError(
                    "The `read_only_fields` option must be a list or tuple. "
                    "Got %s." % type(read_only_fields).__name__
                )

            for field_name in read_only_fields:
                kwargs = extra_kwargs.get(field_name, {})
                kwargs["read_only"] = True
                extra_kwargs[field_name] = kwargs

        return extra_kwargs

    def build_field(self, field_name, info, model_class, nested_depth):
        """
        Return a field or a nested serializer for the field name
        """
        if field_name in info.primary_keys:
            pk = info.primary_keys[field_name]
            return self.build_primary_key_field(field_name, pk)

        elif field_name in info.properties:
            prop = info.properties[field_name]
            return self.build_standard_field(field_name, prop)

        elif field_name in info.relationships:
            relation_info = info.relationships[field_name]
            return self.build_nested_field(field_name, relation_info, nested_depth)

        elif field_name in info.composites:
            composite = info.composites[field_name]
            return self.build_composite_field(field_name, getattr(info.model_class, composite.prop.key))

        elif hasattr(info.model_class, field_name):
            return self.build_property_field(field_name, info)

        elif field_name == self.url_field_name:
            return self.build_url_field(field_name, info)

        return self.build_unknown_field(field_name, info)

    def build_primary_key_field(self, field_name, column_info):
        """
        Builds a field for the primary key of the model
        """
        field_class = self.get_field_type(column_info)

        field_kwargs = self.build_standard_field_kwargs(field_name, field_class, column_info)

        if self.is_nested:
            if self.allow_create or self.allow_null:
                # since we're allowed to create new instances, pk is not required
                field_kwargs["required"] = False

        elif column_info.column.default is not None or column_info.column.autoincrement is True:
            # pk has a default value or its an autoincremented column so the field should be read only
            field_kwargs.pop("required", None)
            field_kwargs["read_only"] = True

        return field_class(**field_kwargs)

    def build_composite_field(self, field_name, composite):
        """
        Builds a `CompositeSerializer` to handle composite attribute in model
        """
        return CompositeSerializer(composite=composite)

    def build_nested_field(self, field_name, relation_info, nested_depth):
        """
        Builds nested serializer to handle relationshipped model
        """
        target_model = relation_info.related_model
        nested_fields = self.get_nested_relationship_fields(relation_info, nested_depth)

        field_kwargs = self.get_relationship_kwargs(relation_info, nested_depth)
        field_kwargs = self.include_extra_kwargs(field_kwargs, self._extra_kwargs.get(field_name))
        nested_extra_kwargs = {}

        nested_info = model_info(target_model)
        if not field_kwargs.get("required", True):
            for nested_field in nested_info.primary_keys:
                nested_extra_kwargs.setdefault(nested_field, {}).setdefault("required", False)

        if not field_kwargs.get("allow_nested_updates", True):
            nested_depth = 0
            for nested_field in nested_info.properties:
                nested_extra_kwargs.setdefault(nested_field, {}).setdefault("read_only", True)
                nested_extra_kwargs.setdefault(nested_field, {}).pop("required", None)

        class NestedSerializer(getattr(self.Meta, "nested_serializer_class", ModelSerializer)):
            class Meta:
                model = target_model
                session = self.session
                depth = max(0, nested_depth - 1)
                fields = nested_fields
                extra_kwargs = nested_extra_kwargs

        return type(str(target_model.__name__ + "Serializer"), (NestedSerializer,), {})(**field_kwargs)

    def build_property_field(self, field_name, info):
        return fields.ReadOnlyField()

    def build_url_field(self, field_name, info):
        """
        Create a field representing the object's own URL.
        """
        field_class = self.serializer_url_field
        field_kwargs = get_url_kwargs(info.model_class)
        field_kwargs.update(self.get_extra_kwargs().get(self.url_field_name, {}))

        return field_class(**field_kwargs)

    def build_unknown_field(self, field_name, info):
        """
        Raise an error on any unknown fields.
        """
        raise ImproperlyConfigured(
            "Field name `%s` is not valid for model `%s`." % (field_name, info.model_class.__name__)
        )

    def get_relationship_kwargs(self, relation_info, depth):
        """
        Figure out the arguments to be used in the `NestedSerializer` for the relationship
        """
        kwargs = {}
        if relation_info.direction == ONETOMANY:
            kwargs["required"] = False
            kwargs["allow_null"] = True
        elif all([col.nullable for col in relation_info.foreign_keys]):
            kwargs["required"] = False
            kwargs["allow_null"] = True

        if relation_info.uselist:
            kwargs["many"] = True
            kwargs["required"] = False

        return kwargs

    def get_nested_relationship_fields(self, relation_info, depth):
        """
        Get the field names for the nested serializer
        """
        target_model_info = model_info(relation_info.related_model)

        # figure out backrefs
        backrefs = set()
        for key, rel in target_model_info.relationships.items():
            if rel.related_model == self.model:
                backrefs.add(key)

        _fields = set(target_model_info.primary_keys.keys())
        _fields.update(target_model_info.properties.keys())
        if depth > 0:
            _fields.update(target_model_info.composites.keys())
            _fields.update(target_model_info.relationships.keys())

        _fields = _fields - backrefs

        return tuple([field for field in _fields if not field.startswith("_")])

    def get_primary_keys(self, validated_data):
        """
        Returns the primary key values from validated_data
        """
        return get_primary_keys(self.model, validated_data) if validated_data else None

    def get_object(self, validated_data, instance=None):
        """
        Returns model object instance using the primary key values in the `validated_data`.
        If the instance is not found, depending on serializer's `allow_create` value, it will create a new model
        instance or raise an error.
        """
        pks = self.get_primary_keys(validated_data)
        checked_instance = None
        if pks:
            checked_instance = self.session.query(self.model).get(pks)
        else:
            checked_instance = instance

        if validated_data is None:
            checked_instance = None

        if checked_instance is not None:
            return checked_instance

        if validated_data is not None and self.allow_create:
            return self.model()

        if self.allow_null:
            return checked_instance

        raise ValidationError("No instance of `{}` found with primary keys `{}`".format(self.model.__name__, pks))

    def save(self, **kwargs):
        """
        Save and return a list of object instances.
        """
        with self.session.no_autoflush:
            self.instance = super(ModelSerializer, self).save(**kwargs)

        self.perform_flush()
        return self.instance

    def perform_flush(self):
        """
        Perform session flush changes
        """
        try:
            self.session.flush()
        except DjangoValidationError as e:
            e = django_to_drf_validation_error(e)
            self._errors = e.detail
            raise e

    def create(self, validated_data):
        """
        Creates a model instance using validated_data
        """
        instance = self.update(self.Meta.model(), validated_data)
        self.session.add(instance)
        return instance

    def update(self, instance, validated_data):
        """
        Updates an existing model instance using validated_data with suspended autoflush
        """
        errors = {}
        instance = self.perform_update(instance, validated_data, errors)

        if errors:
            raise ValidationError(errors)

        return instance

    def perform_update(self, instance, validated_data, errors):
        """
        The main nested update logic implementation using nested fields and serializer
        """
        for field in self._writable_fields:
            if field.source not in validated_data:
                continue

            try:
                value = validated_data.get(field.source)

                if isinstance(field, BaseSerializer):
                    child_instance = getattr(instance, field.source, None)
                    child_instance = field.get_object(value, child_instance)

                    if child_instance and field.allow_nested_updates:
                        value = field.perform_update(child_instance, value, errors)
                    else:
                        value = child_instance

                elif isinstance(field, ListSerializer) and isinstance(field.child, BaseSerializer):

                    value = []

                    for item in validated_data.get(field.source):
                        child_instance = field.child.get_object(item)
                        if child_instance and (field.child.allow_create or field.child.allow_nested_updates):
                            v = field.child.perform_update(child_instance, item, errors)
                        else:
                            v = child_instance

                        if v:
                            value.append(v)

                self.update_attribute(instance, field, value)

            except Exception as e:
                errors.setdefault(field.field_name, []).append(" ".join(map(six.text_type, e.args)))

        return instance
