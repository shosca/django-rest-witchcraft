Django REST Witchcraft
======================

|Build Status| |Read The Docs| |PyPI version| |Coveralls Status|

**SQLAlchemy specific things for django-rest-framework**

Installation
============

::

    pip install django-rest-witchcraft

Quick Start
===========

First up, lets define some simple models:

.. code:: python

    import sqlalchemy as sa
    import sqlalchemy.orm  # noqa
    from sqlalchemy.ext.declarative import declarative_base

    engine = sa.create_engine('sqlite:///:memory:', echo=True)
    session = sa.orm.scoped_session(sa.orm.sessionmaker(bind=engine))

    Base = declarative_base()
    Base.query = session.query_property()


    class Group(Base):
        __tablename__ = 'groups'

        id = sa.Column(sa.Integer(), primary_key=True, autoincrement=True)
        name = sa.Column(sa.String())


    class User(Base):
        __tablename__ = 'users'

        id = sa.Column(sa.Integer(), primary_key=True, autoincrement=True)
        name = sa.Column(sa.String())
        fullname = sa.Column(sa.String())
        password = sa.Column(sa.String())

        _group_id = sa.Column('group_id', sa.Integer(), sa.ForeignKey('groups.id'))
        group = sa.orm.relationship(Group, backref='users')


    class Address(Base):
        __tablename__ = 'addresses'

        id = sa.Column(sa.Integer(), primary_key=True, autoincrement=True)
        email_address = sa.Column(sa.String(), nullable=False)

        _user_id = sa.Column(sa.Integer(), sa.ForeignKey('users.id'))
        user = sa.orm.relationship(User, backref='addresses')

    Base.metadata.create_all(engine)


Nothing fancy here, we have a ``User`` class that can belongs to a ``Group`` instance and has many ``Address``
instances

This serializer can handle nested create, update or partial update operations.

Lets define a serializer for ``User`` with all the fields:

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
        group = GroupSerializer(allow_null=True, is_nested=True, required=False):
            id = IntegerField(allow_null=False, help_text=None, label='Id', required=False)
            name = CharField(allow_null=True, help_text=None, label='Name', max_length=None, required=False)
        addresses = AddressSerializer(allow_null=True, many=True, required=False):
            id = IntegerField(allow_null=False, help_text=None, label='Id', required=False)
            email_address = CharField(allow_null=False, help_text=None, label='Email_address', max_length=None, required=True)
        url = UriField(read_only=True)

Lets try to create a ``User`` instance with our brand new serializer:

.. code:: python

    serializer = UserSerializer(data={
        'name': 'shosca',
        'password': 'swordfish',
    })
    serializer.is_valid()
    serializer.save()

    user = serializer.instance

This will create the following user for us:

::

    >>> user
    User(_group_id=None, id=1, name='shosca', fullname=None, password='swordfish')

Lets try to update our user ``User`` instance and change its password:

.. code:: python

    serializer = UserSerializer(user, data={
        'name': 'shosca',
        'password': 'password',
    })
    serializer.is_valid()
    serializer.save()

    user = serializer.instance

Our user now looks like:

::

    >>> user
    User(_group_id=None, id=1, name='shosca', fullname=None, password='password')

Lets try to update our ``User`` instance again, but this time lets change its password only:

.. code:: python

    serializer = UserSerializer(user, data={
        'password': 'swordfish',
    }, partial=True)
    serializer.is_valid()
    serializer.save()

    user = serializer.instance

This will update the following user for us:

::

    >>> user
    User(_group_id=None, id=1, name='shosca', fullname=None, password='swordfish')

Our user does not belong to a ``Group``, lets fix that:

.. code:: python

    group = Group(name='Admin')
    session.add(group)
    session.flush()

    serializer = UserSerializer(user, data={
        'group': {'id': group.id
    })
    serializer.is_valid()
    serializer.save()

    user = serializer.instance

Now, our user looks like:

::

    >>> user
    User(_group_id=1, id=1, name='shosca', fullname=None, password='swordfish')

    >>> user.group
    Group(id=1, name='Admin')

We can also change the name of our user's group through the user using nested updates:

.. code:: python

    class UserSerializer(serializers.ModelSerializer):

        class Meta:
            model = User
            session = session
            fields = '__all__'
            extra_kwargs = {
                'group': {'allow_nested_updates': True}
            }

    serializer = UserSerializer(user, data={
        'group': {'name': 'Super User'}
    }, partial=True)
    serializer.is_valid()
    serializer.save()

    user = serializer.instance

Now, our user looks like:

::

    >>> user
    User(_group_id=1, id=1, name='shosca', fullname=None, password='swordfish')

    >>> user.group
    Group(id=1, name='Super User')


.. |Build Status| image:: https://travis-ci.org/shosca/django-rest-witchcraft.svg?branch=master
   :target: https://travis-ci.org/shosca/django-rest-witchcraft
.. |Read The Docs| image:: https://readthedocs.org/projects/django-rest-witchcraft/badge/?version=latest
   :target: http://django-rest-witchcraft.readthedocs.io/en/latest/?badge=latest
.. |PyPI version| image:: https://badge.fury.io/py/django-rest-witchcraft.svg
   :target: https://badge.fury.io/py/django-rest-witchcraft
.. |Coveralls Status| image:: https://coveralls.io/repos/github/shosca/django-rest-witchcraft/badge.svg?branch=master
   :target: https://coveralls.io/github/shosca/django-rest-witchcraft?branch=master

