# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import simplejson as json
from django.conf.urls import include, url
from django.test import SimpleTestCase, override_settings
from rest_witchcraft import routers, serializers, viewsets
from sqlalchemy import Column, create_engine, orm, types
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite://')
session = orm.scoped_session(orm.sessionmaker(bind=engine))
Base = declarative_base()
Base.query = session.query_property()


class RouterTestModel(Base):
    __tablename__ = 'routertest'
    id = Column(types.Integer(), default=3, primary_key=True)
    text = Column(types.String(length=200))


class RouterTestCompositeKeyModel(Base):
    __tablename__ = 'routertestcomposite'
    id = Column(types.Integer(), default=1, primary_key=True)
    other_id = Column(types.Integer(), default=3, primary_key=True)
    text = Column(types.String(length=200))


Base.metadata.create_all(engine)


class RouterTestModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = RouterTestModel
        session = session
        fields = '__all__'


class RouterTestCompositeKeyModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = RouterTestCompositeKeyModel
        session = session
        fields = '__all__'


class UnAuthMixin(object):

    def perform_authentication(self, request):
        return None


class RouterTestViewSet(UnAuthMixin, viewsets.ModelViewSet):
    queryset = RouterTestModel.query
    serializer_class = RouterTestModelSerializer


class RouterTestCompositeViewSet(UnAuthMixin, viewsets.ModelViewSet):
    queryset = RouterTestCompositeKeyModel.query
    serializer_class = RouterTestCompositeKeyModelSerializer


class RouterTestCompositeCustomRegexViewSet(UnAuthMixin, viewsets.ModelViewSet):
    queryset = RouterTestCompositeKeyModel.query
    serializer_class = RouterTestCompositeKeyModelSerializer
    lookup_url_regex = '(?P<id>[0-9]+)/other/(?P<other_id>[0-9]+)'


router = routers.DefaultRouter()
router.register(r'test', RouterTestViewSet)
router.register(r'testcomposite', RouterTestCompositeViewSet)
router.register(r'testcompositeregex', RouterTestCompositeCustomRegexViewSet)

urlpatterns = [url(r'^', include(router.urls))]


@override_settings(ROOT_URLCONF='tests.test_routers')
class TestDummyDummy(SimpleTestCase):

    def test_assert_when_no_model_found(self):

        class DummyViewSet(UnAuthMixin, viewsets.ModelViewSet):
            pass

        dummy_router = routers.DefaultRouter()

        with self.assertRaises(AssertionError):
            dummy_router.register(r'dummy', DummyViewSet)

    def test_get_lookup_regex_without_model(self):

        class DummyViewSet(UnAuthMixin, viewsets.ModelViewSet):

            @classmethod
            def get_model(cls):
                return None

        dummy_router = routers.DefaultRouter()

        lookup_regex = dummy_router.get_lookup_regex(DummyViewSet)
        self.assertEqual(lookup_regex, '(?P<pk>[^/.]+)')


@override_settings(ROOT_URLCONF='tests.test_routers')
class TestModelRoutes(SimpleTestCase):

    def setUp(self):
        session.add_all(
            [
                RouterTestModel(id=1, text='router test model 1'),
                RouterTestModel(id=2, text='router test model 2'),
            ]
        )

    def tearDown(self):
        session.rollback()

    def test_list(self):
        resp = self.client.get('/test/')

        self.assertEqual(
            resp.data, [{
                'id': 1,
                'text': 'router test model 1'
            }, {
                'id': 2,
                'text': 'router test model 2'
            }]
        )

    def test_retrieve(self):
        resp = self.client.get('/test/2/')

        self.assertEqual(resp.data, {'id': 2, 'text': 'router test model 2'})

    def test_create(self):
        data = json.dumps({'text': 'router test model 3'})
        resp = self.client.post('/test/', data=data, content_type='application/json')

        self.assertEqual(
            resp.data,
            {'id': 3,
             'text': 'router test model 3'},
        )

    def test_update(self):
        data = {'text': 'router test update 2'}
        resp = self.client.put('/test/2/', data=json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            {'id': 2,
             'text': 'router test update 2'},
        )

    def test_patch_update(self):
        data = {'text': 'router test update 2'}
        resp = self.client.patch('/test/2/', data=json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            {'id': 2,
             'text': 'router test update 2'},
        )

    def test_delete(self):
        resp = self.client.delete('/test/2/', content_type='application/json')
        self.assertEqual(resp.status_code, 204)


@override_settings(ROOT_URLCONF='tests.test_routers')
class TestCompositeRoutes(SimpleTestCase):

    def setUp(self):
        session.add_all(
            [
                RouterTestCompositeKeyModel(id=1, other_id=1, text='router composite model 1'),
                RouterTestCompositeKeyModel(id=1, other_id=2, text='router composite model 2'),
            ]
        )

    def tearDown(self):
        session.rollback()

    def test_list(self):
        resp = self.client.get('/testcomposite/')

        self.assertEqual(
            resp.data, [
                {
                    'id': 1,
                    'other_id': 1,
                    'text': 'router composite model 1'
                }, {
                    'id': 1,
                    'other_id': 2,
                    'text': 'router composite model 2'
                }
            ]
        )

    def test_retrieve(self):
        resp = self.client.get('/testcomposite/1/2/')

        self.assertEqual(resp.data, {'id': 1, 'other_id': 2, 'text': 'router composite model 2'})

    def test_create(self):
        data = json.dumps({'text': 'composite test model 3'})
        resp = self.client.post('/testcomposite/', data=data, content_type='application/json')

        self.assertEqual(
            resp.data,
            {'id': 1,
             'other_id': 3,
             'text': 'composite test model 3'},
        )

    def test_update(self):
        data = json.dumps({'text': 'router test update 2'})
        resp = self.client.put('/testcomposite/1/2/', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            {'id': 1,
             'other_id': 2,
             'text': 'router test update 2'},
        )

    def test_patch_update(self):
        data = json.dumps({'text': 'router test update 2'})
        resp = self.client.patch('/testcomposite/1/2/', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            {'id': 1,
             'other_id': 2,
             'text': 'router test update 2'},
        )

    def test_delete(self):
        resp = self.client.delete('/testcomposite/1/2/', content_type='application/json')
        self.assertEqual(resp.status_code, 204)


@override_settings(ROOT_URLCONF='tests.test_routers')
class TestCompositeRoutesWithCustomRegex(SimpleTestCase):

    def setUp(self):
        session.add_all(
            [
                RouterTestCompositeKeyModel(id=1, other_id=1, text='router composite model 1'),
                RouterTestCompositeKeyModel(id=1, other_id=2, text='router composite model 2'),
            ]
        )

    def tearDown(self):
        session.rollback()

    def test_list(self):
        resp = self.client.get('/testcompositeregex/')

        self.assertEqual(
            resp.data, [
                {
                    'id': 1,
                    'other_id': 1,
                    'text': 'router composite model 1'
                }, {
                    'id': 1,
                    'other_id': 2,
                    'text': 'router composite model 2'
                }
            ]
        )

    def test_retrieve(self):
        resp = self.client.get('/testcompositeregex/1/other/2/')

        self.assertEqual(resp.data, {'id': 1, 'other_id': 2, 'text': 'router composite model 2'})

    def test_create(self):
        data = json.dumps({'text': 'composite test model 3'})
        resp = self.client.post('/testcompositeregex/', data=data, content_type='application/json')

        self.assertEqual(
            resp.data,
            {'id': 1,
             'other_id': 3,
             'text': 'composite test model 3'},
        )

    def test_update(self):
        data = json.dumps({'text': 'router test update 2'})
        resp = self.client.put('/testcompositeregex/1/other/2/', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            {'id': 1,
             'other_id': 2,
             'text': 'router test update 2'},
        )

    def test_patch_update(self):
        data = json.dumps({'text': 'router test update 2'})
        resp = self.client.patch('/testcompositeregex/1/other/2/', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            {'id': 1,
             'other_id': 2,
             'text': 'router test update 2'},
        )

    def test_delete(self):
        resp = self.client.delete('/testcompositeregex/1/other/2/', content_type='application/json')
        self.assertEqual(resp.status_code, 204)
