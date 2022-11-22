from arango import ArangoClient
from arango_orm import Database, Collection, Relation, GraphConnection, Graph
from arango_orm.fields import String, Date


TEST_DB = 'test'

# Initialize the ArangoDB client.
client = ArangoClient()


sys_db = client.db('_system', username='root', password='passwd')

# Connect to the new 'test' database as user 'jane'.
test_db = client.db(TEST_DB, username='root', password='passwd')

db = Database(test_db)

STUDENTS_COLLECTION = 'students'
TEACHERS_COLLECTIONS = 'teachers'
SUBJECTS_COLLECTION = 'subjects'
UNI_GRAPH = 'university_graph'


class Student(Collection):

    __collection__ = STUDENTS_COLLECTION
    _index = [
        {'type': 'hash', 'fields': ['name'], 'unique': False}
    ]

    _key = String(required=True)  # registration number
    name = String(required=True, allow_none=False)
    dob = Date(allow_none=True)


class Teacher(Collection):

    __collection__ = TEACHERS_COLLECTIONS

    _key = String(required=True)  # employee id
    name = String(required=True)


class SpecializesIn(Relation):

    __collection__ = 'specializes_in'

    expertise_level = String(
        required=True,
        options=['expert', 'medium', 'basic']
    )


class Subject(Collection):

    __collection__ = SUBJECTS_COLLECTION

    _key = String(required=True)  # subject code
    name = String(required=True)


class UniversityGraph(Graph):

    __graph__ = UNI_GRAPH

    graph_connections = [
        # Using general Relation class for relationship
        GraphConnection(Student, Relation('studies'), Subject),

        # Using specific classes for vertex and edges
        GraphConnection(Teacher, SpecializesIn, Subject),
    ]
