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
                "select * from pglids.sensor "
                "where type::text = any(%s)", (stype,))
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
    'filename': fields.String,
    'exif': fields.Raw
})


@api.route('/sessions/<int:session_id>/images')
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


@api.route('/itowns/sessions/<int:session_id>/cameras')
class SensorsSession(Resource):

    @api.response(404, 'Session not found')
    def get(self, session_id):
        """List all camera calibrations for a given session"""
        res = Session.query_asdict(
            'select id from pglids.session where id = %s',
            (session_id, )
        )
        if not res:
            api.abort(404, 'Session not found')

        session_id = res[0]['id']

        values = Session.query_aslist(
            """
            with recursive ref as (
                -- get initial referential linked to session
                select
                    rp.id
                    , rp.name
                    , array[rp.id] as ref_list
                    , rp.sensor
                    , '{}'::int[] as transfo_list
                from pglids.session s
                join pglids.platform p on s.platform = p.id
                join pglids.referential rp on rp.platform = p.id
                where s.id = %s -- session id
            union
                -- get all referentials linked by a transformation
                select
                    r.id,
                    r.name,
                    ref_list || r.id as ref_list,
                    r.sensor,
                    transfo_list || t.id
                from ref
                -- join on direct and reverse transformations
                join pglids.transfo t on (t.source = ref.id or t.target = ref.id)
                -- target referential
                join pglids.referential r
                    on (r.id = t.target or r.id = t.source)
                    and not ARRAY[r.id] <@ ref_list -- no cycle
            ), last as (
                select
                    min(ref_list) as ref_list,
                    jsonb_agg(jsonb_build_object(tt.func_name,t.parameters))
                        || jsonb_build_object('id', s.id)
                        || jsonb_build_object('name', s.name)
                        || jsonb_build_object('size_x', s.specifications->'size_x')
                        || jsonb_build_object('size_y', s.specifications->'size_y') as json
                from ref
                join pglids.sensor s on s.id = ref.sensor
                join pglids.transfo t on ref.transfo_list @> ARRAY[t.id]
                join pglids.transfo_type tt on tt.id = t.transfo_type
                where s.type = 'camera'
                group by s.id
            ) select
                json
            from last
                join pglids.datasource ds on
                ds.referential = ref_list[array_upper(ref_list, 1)]
                and ds.session = %s
            """, (session_id, session_id))

        return [
            {key: value for row in rows for key, value in row.items()}
            for rows in values
        ]
