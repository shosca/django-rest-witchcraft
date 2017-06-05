# -*- coding: utf-8 -*-
import enum

from sqlalchemy import Column, ForeignKey, Sequence, create_engine, orm, types
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite://')
session = orm.scoped_session(orm.sessionmaker(bind=engine))

Base = declarative_base()

COLORS = ['red', 'green', 'blue', 'silver']


class Owner(Base):
    __tablename__ = 'owners'

    id = Column(types.Integer(), primary_key=True)
    name = Column(types.String())


class VehicleType(enum.Enum):
    bus = 1
    car = 2


class Engine(object):

    def __init__(self, cylinders, displacement, type_, fuel_type):
        self.cylinders = cylinders
        self.displacement = displacement
        self.type_ = type_
        self.fuel_type = fuel_type

    def __composite_values__(self):
        return self.cylinders, self.displacement, self.type_, self.fuel_type

    def __repr__(self):
        return 'Engine(cylinder={},displacement={},displacement_liters={},type="{}",fuel_type="{}"'.format(
            *self.__composite_values__()
        )

    def __eq__(self, other):
        return isinstance(other, Engine) and other.__composite_values__() == self.__composite_values__()


class Vehicle(Base):
    __tablename__ = 'vehicles'

    id = Column(types.Integer(), Sequence('seq_id'), primary_key=True, doc='The primary key')
    name = Column(types.String(), doc='The name of the vehicle')
    type = Column(types.Enum(VehicleType), nullable=False)
    created_at = Column(types.DateTime())
    paint = Column(types.Enum(*COLORS))

    @property
    def lower_name(self):
        return self.name.lower()

    _engine_cylinders = Column('engine_cylinders', types.BigInteger())
    _engine_displacement = Column('engine_displacement', types.Numeric(asdecimal=True, precision=10, scale=2))
    _engine_type = Column('engine_type', types.String(length=25))
    _engine_fuel_type = Column('engine_fuel_type', types.String(length=10))
    engine = orm.composite(Engine, _engine_cylinders, _engine_displacement, _engine_type, _engine_fuel_type)

    _owner_id = Column('owner_id', types.Integer(), ForeignKey(Owner.id))
    owner = orm.relationship(Owner, backref='vehicles')


class VehicleOther(Base):
    __tablename__ = 'vehicle_other'

    id = Column(types.Integer(), primary_key=True, doc='The primary key')

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
    vehicle = orm.relationship(Vehicle, backref=orm.backref('other', uselist=False), uselist=False)


class Option(Base):
    __tablename__ = 'options'
    id = Column(types.Integer(), primary_key=True)
    name = Column(types.String())

    _vehicle_id = Column(types.Integer(), ForeignKey(Vehicle.id))
    vehicle = orm.relationship(Vehicle, backref='options')


Base.metadata.create_all(engine)
