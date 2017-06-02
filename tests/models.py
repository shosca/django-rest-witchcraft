# -*- coding: utf-8 -*-
import enum

from sqlalchemy import Column, ForeignKey, Sequence, create_engine, types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, composite, relationship, scoped_session, sessionmaker

engine = create_engine('sqlite://')
session = scoped_session(sessionmaker(bind=engine))

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

    def __init__(self, cylinders, displacement_ci, displacement_liters, type_):
        self.cylinders = cylinders
        self.displacement_ci = displacement_ci
        self.displacement_liters = displacement_liters
        self.type_ = type_

    def __composite_values__(self):
        return self.cylinders, self.displacement_ci, self.displacement_liters, self.type_

    def __repr__(self):
        return 'Engine(cylinder={},displacement_ci={},displacement_liters={},type={}'.format(
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

    _engn_cylinders = Column('engn_cylinders_nb', types.BigInteger())
    _engn_dsplmt_ci = Column('engn_dsplmt_ci_nb', types.Numeric(asdecimal=True, precision=10, scale=2))
    _engn_dsplmt_l = Column('engn_dsplmt_l_nb', types.Numeric(asdecimal=True, precision=10, scale=2))
    _engn_type = Column('engn_typ_nm', types.String(length=25))
    _fuel_type = Column('fuel_typ_nm', types.String(length=10))
    engine = composite(Engine, _engn_cylinders, _engn_dsplmt_ci, _engn_dsplmt_l, _engn_type, _fuel_type)

    _owner_id = Column('owner_id', types.Integer(), ForeignKey(Owner.id))
    owner = relationship(Owner, backref='vehicles')


class VehicleOther(Base):
    __tablename__ = 'vehicle_other'

    id = Column(types.Integer(), ForeignKey(Vehicle.id), primary_key=True, doc='The primary key')

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

    vehicle = relationship(Vehicle, backref=backref('other', uselist=False), uselist=False)


class Option(Base):
    __tablename__ = 'options'
    id = Column(types.Integer(), primary_key=True)
    name = Column(types.String())

    _vehicle_id = Column(types.Integer(), ForeignKey(Vehicle.id))
    vehicle = relationship(Vehicle, backref='options')


Base.metadata.create_all(engine)
