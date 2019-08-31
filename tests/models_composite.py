# -*- coding: utf-8 -*-

from sqlalchemy import Column, create_engine, orm, types
from sqlalchemy.ext.declarative import declarative_base


engine = create_engine("sqlite://")
session = orm.scoped_session(orm.sessionmaker(bind=engine))
Base = declarative_base()
Base.query = session.query_property()


class RouterTestModel(Base):
    __tablename__ = "routertest"
    id = Column(types.Integer(), default=3, primary_key=True)
    text = Column(types.String(length=200))


class RouterTestCompositeKeyModel(Base):
    __tablename__ = "routertestcomposite"
    id = Column(types.Integer(), default=1, primary_key=True)
    other_id = Column(types.Integer(), default=3, primary_key=True)
    text = Column(types.String(length=200))


Base.metadata.create_all(engine)
