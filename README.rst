Django REST Witchcraft
======================

|Build Status| |Read The Docs| |PyPI version|

**SQLAlchemy specific things for django-rest-framework**

Installation
============

::

    pip install django-rest-witchcraft

Quick Start
===========

First up, lets define some simple models:

.. code:: python

    engine = create_engine('sqlite:///:memory:', echo=True)
    session = scoped_session(sessionmaker(bind=engine))

    Base = declarative_base()
    Base.query = session.query_property()

    Base.metadata.create_all(engine)

    class Group(Base):
        __tablename__ = 'groups'

        id = Column(Integer(), primary_key=True)
        name = Column(String())


    class User(Base):
        __tablename__ = 'users'

        id = Column(Integer(), primary_key=True)
        name = Column(String())
        fullname = Column(String())
        password = Column(String())

        _group_id = Column('group_id', Integer(), ForeignKey('groups.id'))
        group = relationship(Group, backref='users')


    class Address(Base):
        __tablename__ = 'addresses'

        id = Column(Integer(), primary_key=True)
        email_addresss = Column(String(), nullable=False)

        _user_id = Column(Integer(), ForeignKey('users.id'))
        user = relationship(User, backref='addresses')

Nothing fancy here, we have a ``User`` class that can belong to a
``Group`` instance and has many ``Address`` instances

Second, lets define a serializer for ``User`` with all the fields:

.. code:: python

    class UserSerializer(serializers.ModelSerializer):

        class Meta:
            model = User
            session = session
            fields = '__all__'

This will create the following serializer for us:

::

    >>> serializer = UserSerializer()

    >>> serializer
    UserSerializer():
        id = IntegerField(allow_null=False, help_text=None, label='Id', required=True)
        name = CharField(allow_null=True, help_text=None, label='Name', max_length=None, required=False)
        fullname = CharField(allow_null=True, help_text=None, label='Fullname', max_length=None, required=False)
        password = CharField(allow_null=True, help_text=None, label='Password', max_length=None, required=False)
        group = GroupSerializer(is_nested=True, required=False):
            name = CharField(allow_null=True, help_text=None, label='Name', max_length=None, required=False)
            id = IntegerField(allow_null=False, help_text=None, label='Id', required=False)
        addresses = AddressSerializer(many=True, required=False):
            id = IntegerField(allow_null=False, help_text=None, label='Id', required=False)
            email_addresss = CharField(allow_null=False, help_text=None, label='Email_addresss', max_length=None, required=True)
        url = UriField(read_only=True)

This serializer can handle nested create, update or partial update
operations.

.. |Build Status| image:: https://travis-ci.org/shosca/django-rest-witchcraft.svg?branch=master
   :target: https://travis-ci.org/shosca/django-rest-witchcraft
.. |Read The Docs| image:: https://readthedocs.org/projects/django-rest-witchcraft/badge/?version=latest
   :target: http://django-rest-witchcraft.readthedocs.io/en/latest/?badge=latest
.. |PyPI version| image:: https://badge.fury.io/py/django-rest-witchcraft.svg
   :target: https://badge.fury.io/py/django-rest-witchcraft
