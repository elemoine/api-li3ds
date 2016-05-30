# -*- coding: utf-8 -*-
from flask.ext.restplus import Api, Resource, fields
from psycopg2.extensions import AsIs

from .database import Session


api = Api(
    version='1.0', title='LI3DS API',
    description='API for accessing LI3DS metadata',
)


@api.route('/projects')
class Projects(Resource):
    def get(self):
        return Session.query_asdict("select * from pglids.project")


@api.route('/sessions')
class Sessions(Resource):
    def get(self):
        return Session.query_asdict("select * from pglids.session")


@api.route('/platforms')
class Platforms(Resource):
    def get(self):
        return Session.query_asdict("select * from pglids.platform")


@api.route('/sensors')
class Sensors(Resource):
    def get(self):
        return Session.query_asdict("select * from pglids.sensor")


@api.route('/referentials')
class Referentials(Resource):
    def get(self):
        return Session.query_asdict("select * from pglids.referential")

transfo_model = api.model('Transfo Model', {
    'id': fields.Integer,
    'source': fields.Integer,
    'target': fields.Integer,
    'transfo_type': fields.Integer,
    'description': fields.String,
    'parameters': fields.Raw,
    'tdate': fields.DateTime(dt_format='iso8601'),
    'validity_start': fields.DateTime(dt_format='iso8601'),
    'validity_end': fields.DateTime(dt_format='iso8601'),
})


@api.route('/transfos')
class Transfos(Resource):
    @api.marshal_with(transfo_model)
    def get(self):
        return Session.query_asdict("select * from pglids.transfo")


@api.route('/images/<string:project>')
class Images(Resource):
    def get(self, project):
        return Session.query_asdict('select * from %s.image', [AsIs(project)])
