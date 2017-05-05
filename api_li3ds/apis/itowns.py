# -*- coding: utf-8 -*-
from flask import request
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


@nsitowns.route('/v1/sessions/<int:session_id>/images')
class Images(Resource):

    @nsitowns.response(404, 'Session not found')
    def get(self, session_id):
        '''List all images in a given session with their location'''
        # get project name
        res = Database.query("""
            select p.id, p.name from li3ds.project p
            join li3ds.session s on s.project = p.id
            where s.id = %s
            """, (session_id, ))

        if not res:
            nsitowns.abort(404, 'Session not found')

        project_name, project_id = res[0].name, res[0].id

        return Database.query_asjson(
            """
            with images as (
                -- extract image epoch
                select
                    i.id,
                    i.filename,
                    i.etime,
                    extract(epoch from etime) as epoch,
                    rf.sensor
                from %(project)s.image i
                join li3ds.datasource ds on i.datasource = ds.id
                join li3ds.referential rf on ds.referential = rf.id
                where ds.session = %(session)s
            ), route as (
                -- get latest route
                select r.points as points
                from %(project)s.route r
                join li3ds.datasource ds on r.datasource = ds.id
                join li3ds.session s on ds.session = s.id
                join li3ds.project p on s.project = p.id
                where p.id = %(project_id)s
                order by ds.id desc limit 1
            )
            select
                i.id,
                i.filename,
                i.etime as date,
                i.sensor,
                pc_get(newpt, 'x') as easting,
                pc_get(newpt, 'y') as northing,
                pc_get(newpt, 'z') as altitude,
                pc_get(newpt, 'm_roll') as roll,
                pc_get(newpt, 'm_pitch') as pitch,
                pc_get(newpt, 'm_plateformHeading')
                    - pc_get(newpt, 'm_wanderAngle') as heading
            from route r
            join images i on i.etime <@ tstzrange(r.start_time, r.end_time),
            pc_interpolate(r.points, 'm_time', i.epoch) as newpt
            """,
            ({'project': AsIs(project_name),
              'project_id': project_id,
              'session': session_id})
        )


@nsitowns.route('/v1/sessions/<int:session_id>/cameras')
@nsitowns.doc(params={
    'platform_config': 'platform configuration identifier',
})
class SensorsSession(Resource):

    @nsitowns.response(500, 'parameter required : platform_config')
    def get(self, session_id):
        '''List all camera calibrations for a given session'''
        if 'platform_config' not in request.args:
            nsitowns.abort(500, 'parameter required : platform_config')
        # get all cameras for this platform configuration

        values = Database.query_asjson("""
            with transfos as (
                -- all transformations for this platform config
                select
                    unnest(tt.transfos) as tid
                from li3ds.platform_config pf
                join li3ds.transfo_tree tt on tt.id = ANY(pf.transfo_trees)
                where pf.id = %(pconfig)s
            ), ins_transfo as (
                -- get ins first transformation
                select trlist.tid as target
                from transfos trlist
                join li3ds.transfo tr on tr.id = trlist.tid
                join li3ds.referential r on tr.source = r.id or tr.target = r.id
                join li3ds.sensor s on s.id = r.sensor
                where s.type = 'ins' and r.root
            ), camera_transfo as (
                -- get all camera first transformations
                select tr.id as source, se.*
                from li3ds.session s
                join li3ds.datasource ds on ds.session = s.id
                join li3ds.referential r on r.id = ds.referential
                join li3ds.sensor se on se.id = r.sensor
                join li3ds.transfo tr on tr.source = r.id or tr.target = r.id
                join transfos trlist on trlist.tid = tr.id
                where s.id = %(session)s and se.type = 'camera'
            )
            select
                id
                , ARRAY[specifications->'size_x', specifications->'size_y'] as size
                , _.transfos
            from
                camera_transfo
                , ins_transfo
                , li3ds.dijkstra(%(pconfig)s, source, target) as path
                , lateral (
                    select jsonb_agg(row_to_json(s)) as transfos from
                    (
                        select t.id, t.parameters, tt.description, tt.func_name as type
                         from unnest(path) with ordinality as u(tid, ord)
                         join li3ds.transfo t on t.id = tid
                         join li3ds.transfo_type tt on tt.id = t.transfo_type
                     ) as s
                ) as _
            """, ({'pconfig': request.args['platform_config'], 'session': session_id}))

        return values
