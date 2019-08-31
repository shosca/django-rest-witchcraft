# -*- coding: utf-8 -*-
import enum

from sqlalchemy import Column, ForeignKey, Sequence, orm, types

from django.core.exceptions import ValidationError

from django_sorcery.db import SQLAlchemy
from django_sorcery.db.models import autocoerce


session = SQLAlchemy("postgresql://postgres@localhost/test")

Base = session.Model

COLORS = ["red", "green", "blue", "silver"]


class Owner(Base):
    __tablename__ = "owners"

    id = Column(types.Integer(), primary_key=True)
    first_name = Column(types.Unicode(length=50))
    last_name = Column(types.Unicode(length=50))


class VehicleType(enum.Enum):
    bus = "Bus"
    car = "Car"


class Engine(object):
    def __init__(self, cylinders, displacement, type_, fuel_type):
        self.cylinders = cylinders
        self.displacement = displacement
        self.type_ = type_
        self.fuel_type = fuel_type

    def __composite_values__(self):
        return self.cylinders, self.displacement, self.type_, self.fuel_type

    def __repr__(self):
        return 'Engine(cylinder={},displacement={},type="{}",fuel_type="{}")'.format(*self.__composite_values__())

    def __eq__(self, other):
        return isinstance(other, Engine) and other.__composite_values__() == self.__composite_values__()


@autocoerce
class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(types.Integer(), Sequence("seq_id"), primary_key=True, doc="The primary key")
    name = Column(types.String(length=50), doc="The name of the vehicle")
    type = Column(types.Enum(VehicleType, name="vehicle_type"), nullable=False)
    created_at = Column(types.DateTime())
    paint = Column(types.Enum(*COLORS, name="colors"))
    is_used = Column(types.Boolean)

    @property
    def lower_name(self):
        return self.name.lower()

    _engine_cylinders = Column("engine_cylinders", types.BigInteger())
    _engine_displacement = Column("engine_displacement", types.Numeric(asdecimal=True, precision=10, scale=2))
    _engine_type = Column("engine_type", types.String(length=25))
    _engine_fuel_type = Column("engine_fuel_type", types.String(length=10))
    engine = orm.composite(Engine, _engine_cylinders, _engine_displacement, _engine_type, _engine_fuel_type)

    _owner_id = Column("owner_id", types.Integer(), ForeignKey(Owner.id))
    owner = orm.relationship(Owner, backref="vehicles")

    def clean_name(self):
        if self.name == "invalid":
            raise ValidationError("invalid vehicle name")


class VehicleOther(Base):
    __tablename__ = "vehicle_other"

    id = Column(types.Integer(), primary_key=True, doc="The primary key")

    advertising_cost = Column(types.BigInteger())
    base_invoice = Column(types.BigInteger())
    base_msrp = Column(types.BigInteger())
    destination_charge = Column(types.BigInteger())
    gas_guzzler_tax = Column(types.BigInteger())
    list_price = Column(types.BigInteger())
    misc_cost = Column(types.BigInteger())
    options_invoice = Column(types.BigInteger())
    options_msrp = Column(types.BigInteger())
    package_discount = Column(types.BigInteger())
    prep_cost = Column(types.BigInteger())
    total_msrp = Column(types.BigInteger())
    vehicle_invoice = Column(types.BigInteger())
    vehicle_msrp = Column(types.BigInteger())

    _vehicle_id = Column(types.Integer(), ForeignKey(Vehicle.id))
    vehicle = orm.relationship(Vehicle, backref=orm.backref("other", uselist=False), uselist=False)


class Option(Base):
    __tablename__ = "options"
    id = Column(types.Integer(), primary_key=True)
    name = Column(types.String(length=50))

    _vehicle_id = Column(types.Integer(), ForeignKey(Vehicle.id))
    vehicle = orm.relationship(Vehicle, backref="options")


class ModelWithJson(Base):
    __tablename__ = "model_with_json"

    id = Column(types.Integer(), Sequence("seq_id"), primary_key=True)


session.create_all()

# getting around sqlite not supporting json column
ModelWithJson.js = Column(types.JSON())
