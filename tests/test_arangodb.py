import unittest

import factory
from factory.arangodb import (
    ArangoDBCollectionFactory, ArangoDBEdgeFactory,
    ArangoDBEdgeWithAttrsFactory
)
from arango_orm import Relation

from .arangodbapp import models


COLLECTIONS = (
    models.STUDENTS_COLLECTION,
    models.TEACHERS_COLLECTIONS,
    models.SUBJECTS_COLLECTION
)


class StudentFactory(ArangoDBCollectionFactory):
    class Meta:
        model = models.Student
        db_session = models.db

    _key = factory.Sequence(lambda n: "key_%d" % n)
    name = factory.Sequence(lambda n: "name_%d" % n)


class TeacherFactory(ArangoDBCollectionFactory):
    class Meta:
        model = models.Teacher
        db_session = models.db

    _key = factory.Sequence(lambda n: "key_%d" % n)
    name = factory.Sequence(lambda n: "name_%d" % n)


class SubjectFactory(ArangoDBCollectionFactory):
    class Meta:
        model = models.Subject
        db_session = models.db

    _key = factory.Sequence(lambda n: "key_%d" % n)
    name = factory.Sequence(lambda n: "name_%d" % n)


class TeacherSpecializesInSubjectFactory(ArangoDBEdgeWithAttrsFactory):
    class Meta:
        model = models.SpecializesIn
        graph = models.UniversityGraph
        db_session = models.db

    _from = factory.SubFactory(TeacherFactory)
    _to = factory.SubFactory(SubjectFactory)
    expertise_level = 'medium'


class StudentStudiesSubjectFactory(ArangoDBEdgeFactory):
    class Meta:
        model = Relation("studies")
        graph = models.UniversityGraph
        db_session = models.db

    _key = factory.Sequence(lambda n: "key_%d" % n)
    _from = factory.SubFactory(StudentFactory)
    _to = factory.SubFactory(SubjectFactory)



class BaseTestCase(unittest.TestCase):
    def setUp(self):
        # Create a new database named "test" if it does not exist.
        # Only root user has access to it at time of its creation.
        if not models.sys_db.has_database(models.TEST_DB):
            models.sys_db.create_database(models.TEST_DB)

        for col in COLLECTIONS:
            if not models.test_db.has_collection(col):
                models.test_db.create_collection(col)

        # create graph
        graph = models.UniversityGraph(connection=models.db)
        models.db.create_graph(graph, ignore_collections=COLLECTIONS)

    def tearDown(self):
        models.sys_db.delete_database(models.TEST_DB)
        models.client.close()


class ArrangoDBTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        StudentFactory.reset_sequence(1)

    def test_build(self):
        std = StudentFactory.build()
        self.assertEqual('name_1', std.name)
        self.assertEqual('key_1', std._key)

        self.assertEqual(models.db.query(models.Student).count(), 0)

    def test_create(self):
        std = StudentFactory.create()
        self.assertEqual('name_1', std.name)
        self.assertEqual('key_1', std._key)

        self.assertEqual(models.db.query(models.Student).count(), 1)

    def test_many_build(self):
        std1 = StudentFactory.build()
        std2 = StudentFactory.build()
        self.assertEqual('name_1', std1.name)
        self.assertEqual('name_2', std2.name)



class EdgeFirstWithAttributesTestCase(BaseTestCase):
    """Test custom attributes in Relation.

    This test should be before EdgeTestCase
    becuase of bug with dumping extra attributes in custom Relation.
    """

    def test_create(self):
        edge = TeacherSpecializesInSubjectFactory.create()
        self.assertIsNotNone(edge.get('_key'))
        self.assertEqual(models.db.query(Relation('specializes_in')).count(), 1)

    def test_create_with_params(self):
        TeacherSpecializesInSubjectFactory.create()
        edge = models.db.query(models.SpecializesIn).first()

        self.assertEqual(edge.expertise_level, 'medium')


class EdgeTestCase(BaseTestCase):
    def test_create(self):
        edge = StudentStudiesSubjectFactory.create()
        self.assertIsNotNone(edge.get('_key'))
        self.assertEqual(models.db.query(Relation('studies')).count(), 1)

    def test_create_subfactories(self):
        StudentStudiesSubjectFactory.create()
        edge = models.db.query(Relation('studies')).first()
        self.assertIsNotNone(edge)
        self.assertIsNotNone(models.db.query(models.Student).by_key(edge._from))
        self.assertIsNotNone(models.db.query(models.Subject).by_key(edge._to))

    def test_create_with_params(self):
        std = StudentFactory()
        subj = SubjectFactory()
        StudentStudiesSubjectFactory.create(_from=std, _to=subj)

        edge = (
            models.db.query(Relation('studies'))
            .filter("_from==@_from", _from=std._id)
            .filter("_to==@_to", _to=subj._id)
            .first()
        )

        self.assertIsNotNone(edge)
        self.assertEqual(edge._from, std._id)
        self.assertEqual(edge._to, subj._id)
