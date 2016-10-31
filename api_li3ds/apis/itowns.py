# -*- coding: utf-8 -*-
from flask_restplus import fields
from psycopg2.extensions import AsIs

from api_li3ds.app import api, Resource
from api_li3ds.database import Database


nsitowns = api.namespace('itowns', description='itowns facilities')


image_model = nsitowns.model('Image', {
    'id': fields.Integer,
    'filename': fields.String,
    'exif': fields.Raw
})


@nsitowns.route('/sessions/<int:session_id>/images')
class Images(Resource):

    @nsitowns.marshal_with(image_model)
    @nsitowns.response(404, 'Session not found')
    def get(self, session_id):
        '''List all images in given session'''
        res = Database.query_asdict(
            'select p.name, s.id from li3ds.session s '
            'join li3ds.project p on s.project = p.id '
            'where s.id = %s',
            (session_id, )
        )
        if not res:
            nsitowns.abort(404, 'Session not found')

        project, session_id = res[0]['name'], res[0]['id']

        return Database.query_asdict(
            'select i.* from %s.image i '
            'join li3ds.datasource d on d.session = %s and d.id = i.datasource',
            (AsIs(project), session_id)
        )


@nsitowns.route('/sessions/<int:session_id>/cameras')
class SensorsSession(Resource):

    @nsitowns.response(404, 'Session not found')
    def get(self, session_id):
        '''List all camera calibrations for a given session'''
        res = Database.query_asdict(
            'select id from li3ds.session where id = %s',
            (session_id, )
        )
        if not res:
            nsitowns.abort(404, 'Session not found')

        session_id = res[0]['id']

        values = Database.query_aslist(
            '''
            with recursive ref as (
                -- get initial referential linked to session
                select
                    rp.id
                    , rp.name
                    , array[rp.id] as ref_list
                    , rp.sensor
                    , '{}'::int[] as transfo_list
                from li3ds.session s
                join li3ds.platform p on s.platform = p.id
                -- à remplacer par datasource
                join li3ds.referential rp on rp.platform = p.id
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
                join li3ds.transfo t on (t.source = ref.id or t.target = ref.id)
                -- target referential
                join li3ds.referential r
                    on (r.id = t.target or r.id = t.source)
                    and not ARRAY[r.id] <@ ref_list -- no cycle
            ), last as (
                select
                    min(ref_list) as ref_list,
                    jsonb_agg(jsonb_build_object(tt.func_name,t.parameters))
                        || jsonb_build_object('id', s.id)
                        || jsonb_build_object('short_name', s.short_name)
                        || jsonb_build_object('model', s.model)
                        || jsonb_build_object('size_x', s.specifications->'size_x')
                        || jsonb_build_object('size_y', s.specifications->'size_y') as json
                from ref
                join li3ds.sensor s on s.id = ref.sensor
                join li3ds.transfo t on ref.transfo_list @> ARRAY[t.id]
                join li3ds.transfo_type tt on tt.id = t.transfo_type
                where s.type = 'camera'
                group by s.id
            ) select
                json
            from last
                join li3ds.datasource ds on
                ds.referential = ref_list[array_upper(ref_list, 1)]
                and ds.session = %s
            ''', (session_id, session_id))

        return [
            {key: value for row in rows for key, value in row.items()}
            for rows in values
        ]
