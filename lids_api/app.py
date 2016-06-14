# -*- coding: utf-8 -*-
from flask import request
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
        """List projects"""
        return Session.query_asdict("select * from pglids.project")

session_model = api.model('Session Model', {
    'id': fields.Integer,
    'name': fields.String,
    'start_time': fields.DateTime(dt_format='iso8601'),
    'end_time': fields.DateTime(dt_format='iso8601'),
})


@api.route('/sessions')
class Sessions(Resource):
    @api.marshal_with(session_model)
    def get(self):
        """List sessions"""
        return Session.query_asdict("select * from pglids.session")


@api.route('/platforms')
class Platforms(Resource):
    def get(self):
        """List platforms"""
        return Session.query_asdict("select * from pglids.platform")


@api.route('/sensor_types')
class Sensor_types(Resource):
    def get(self):
        """Sensor type list"""
        return Session.query_aslist(
            """select unnest(enum_range(enum_first(null::pglids.sensor_type),
            null::pglids.sensor_type))"""
        )


@api.route('/sensors')
@api.param('type', 'sensor type (camera, lidar, ins...')
class Sensors(Resource):
    def get(self):
        """List sensors"""
        stype = [
            typ.strip().lower() for typ in
            request.args.get('type', '').split(',') if typ
        ]
        if stype:
            return Session.query_asdict(
                "select * from pglids.sensor where type::text = any(%s)", (stype,))
        else:
            return Session.query_asdict("select * from pglids.sensor")


@api.route('/referentials')
class Referentials(Resource):
    def get(self):
        """List referentials"""
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
        """List transformations between referentials"""
        return Session.query_asdict("select * from pglids.transfo")


image_model = api.model('Image', {
    'id': fields.Integer,
    'exif': fields.Raw
})


@api.route('/sessions/<int:session_id>/images')
@api.doc()
class Images(Resource):
    @api.marshal_with(image_model)
    @api.response(404, 'Session not found')
    def get(self, session_id):
        """List all images in given session"""
        res = Session.query_asdict(
            'select p.name, s.id from pglids.session s '
            'join pglids.project p on s.project = p.id '
            'where s.id = %s',
            (session_id, )
        )
        if not res:
            api.abort(404, 'Session not found')

        project, session_id = res[0]['name'], res[0]['id']

        return Session.query_asdict(
            'select i.* from %s.image i '
            'join pglids.datasource d on d.session = %s and d.id = i.datasource',
            (AsIs(project), session_id)
        )
