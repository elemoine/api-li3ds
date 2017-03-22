# -*- coding: utf-8 -*-
from flask import make_response
from flask import url_for
from flask_restplus import fields
from graphviz import Digraph

from api_li3ds.app import api, Resource, defaultpayload
from api_li3ds.database import Database
from .sensor import sensor_model

nspfm = api.namespace('platforms', description='platforms related operations')

platform_model_post = nspfm.model(
    'Platform Model Post',
    {
        'name': fields.String,
        'description': fields.String,
        'start_time': fields.DateTime(dt_format='iso8601', default=None),
        'end_time': fields.DateTime(dt_format='iso8601', default=None),
    })

platform_model = nspfm.inherit(
    'Platform Model',
    platform_model_post,
    {
        'id': fields.Integer
    })

platform_config_post = nspfm.model(
    'Platform Config Post',
    {
        'name': fields.String,
        'owner': fields.String,
        'transfo_trees': fields.List(fields.Integer)
    })

platform_config = nspfm.inherit(
    'Platform Config',
    platform_config_post,
    {
        'id': fields.Integer,
    })


def platform_config_dot(id):

    config = Database.query(
        "select * from li3ds.platform_config where id = %s", (id,)
    )
    if not config:
        return nspfm.abort(404, 'Platform configuration not found')
    config = config[0]

    edges = Database.query(
        """
        select t.id, t.source, t.target, t.transfo_type, tf.sc, tft.name
        from (
            select distinct
                unnest(tt.transfos) as tid, sensor_connections as sc
            from li3ds.transfo_tree tt where tt.id = ANY(%s)
        ) as tf
        join li3ds.transfo t on t.id = tf.tid
        join li3ds.transfo_type tft on tft.id = t.transfo_type
        """, (list(config.transfo_trees), )
    )
    urefs = set()
    for edge in edges:
        urefs.add(edge.source)
        urefs.add(edge.target)

    nodes = Database.query("""
        select distinct r.id, r.name, r.root, r.sensor, s.name as sensor_name
        from li3ds.referential r
        join li3ds.sensor s on r.sensor = s.id
        where ARRAY[r.id] <@ %s
    """, (list(urefs), ))

    url = url_for('platform_config_dot', id=id, _external=True)
    dot = Digraph(name="config_{}".format(id), comment=url)
    dot.graph_attr.update({
        'label': "Platform {} : {} ({})".format(config.platform, config.name, config.id),
        'overlap': 'scalexy'
    })

    subgraphs = {}

    for node in nodes:
        if node.sensor not in subgraphs:
            subgraphs[node.sensor] = Digraph(name="cluster_{}".format(node.sensor))
            subgraphs[node.sensor].graph_attr.update({
                'label': "{} ({})".format(node.sensor_name, node.sensor)
            })
        color = 'red' if node.root else 'black'
        subgraphs[node.sensor].node(str(node.id), '{}\n({})'.format(node.name, node.id), color=color)
        dot.subgraph(subgraphs[node.sensor])

    for edge in edges:
        # highlight sensor connections in blue
        color = 'blue' if edge.sc else 'black'
        dot.edge(
            str(edge.source),
            str(edge.target),
            label='{}\n({})'.format(edge.name, edge.id),
            color=color)

    dot.engine = 'dot'
    return dot


@nspfm.route('/', endpoint='platforms')
class Platforms(Resource):

    @nspfm.marshal_with(platform_model)
    def get(self):
        '''List platforms'''
        return Database.query_asjson("select * from li3ds.platform")

    @api.secure
    @nspfm.expect(platform_model_post)
    @nspfm.marshal_with(platform_model)
    @nspfm.response(201, 'Platform created')
    def post(self):
        '''Create a platform'''
        return Database.query_asdict(
            "insert into li3ds.platform (name, description, start_time, end_time) "
            "values (%(name)s, %(description)s, %(start_time)s, %(end_time)s) "
            "returning *",
            defaultpayload(api.payload)
        ), 201


@nspfm.route('/<int:id>/', endpoint='platform')
@nspfm.response(404, 'Platform not found')
class OnePlatform(Resource):

    @nspfm.marshal_with(platform_model)
    def get(self, id):
        '''Get one platform given its identifier'''
        res = Database.query_asjson(
            "select * from li3ds.platform where id=%s", (id,)
        )
        if not res:
            nspfm.abort(404, 'Platform not found')
        return res

    @api.secure
    @nspfm.response(410, 'Platform deleted')
    def delete(self, id):
        '''Delete a platform given its identifier'''
        res = Database.rowcount("delete from li3ds.platform where id=%s", (id,))
        if not res:
            nspfm.abort(404, 'Platform not found')
        return '', 410


@nspfm.route('/<int:id>/configs/', endpoint='platform_configs')
class PlatformConfigs(Resource):

    @nspfm.marshal_with(platform_config)
    def get(self, id):
        '''List all platform configurations'''
        return Database.query_asjson(
            "select * from li3ds.platform_config where platform = %s", (id,)
        )

    @api.secure
    @nspfm.expect(platform_config_post)
    @nspfm.marshal_with(platform_config)
    def post(self, id):
        '''Create a new platform configuration'''
        return Database.query_asdict(
            "insert into li3ds.platform_config (name, owner, platform, transfo_trees) "
            "values (%(name)s, %(owner)s, {}, %(transfo_trees)s) "
            "returning *".format(id),
            defaultpayload(api.payload)
        ), 201


@nspfm.route('/configs/<int:id>/', endpoint='platform_config')
@nspfm.param('id', 'The platform config identifier')
class OnePlatformConfig(Resource):

    def get(self, id):
        '''Get a platform configuration given its identifier'''
        return Database.query_asjson(
            "select * from li3ds.platform_config where id = %s", (id,)
        )

    @api.secure
    @nspfm.response(410, 'Platform configuration deleted')
    def delete(self, id):
        '''Delete a platform configuration given its identifier'''
        res = Database.rowcount("delete from li3ds.platform_config where id=%s", (id,))
        if not res:
            nspfm.abort(404, 'Platform configuration not found')
        return '', 410


@nspfm.route('/configs/<int:id>/dot/', endpoint='platform_config_dot')
@nspfm.param('id', 'The platform config identifier')
class PlatformConfigDot(Resource):

    def get(self, id):
        '''Get a preview for this platform configuration as dot

        Nodes are referentials and edges are tranformations between referentials.
        Blue arrows represents connections between sensors (or sensor groups).
        Red nodes are root referentials
        '''
        response = make_response(platform_config_dot(id).source)
        response.headers['content-type'] = 'text/plain'
        response.mimetype = 'text/plain'
        return response


@nspfm.route('/configs/<int:id>/preview/', endpoint='platform_config_preview')
@nspfm.param('id', 'The platform config identifier')
class PlatformConfigPreview(Resource):

    def get(self, id):
        '''Get a preview for this platform configuration as png

        Nodes are referentials and edges are tranformations between referentials.
        Blue arrows represents connections between sensors (or sensor groups).
        Red nodes are root referentials
        '''
        dot = platform_config_dot(id)
        data = dot.pipe("png")

        response = make_response(data)
        response.headers['content-type'] = 'image/png'
        response.mimetype = 'image/png'
        return response


@nspfm.route('/configs/<int:id>/sensors/', endpoint='platform_config_sensors')
@nspfm.param('id', 'The platform config identifier')
class PlatformConfigSensors(Resource):

    @nspfm.marshal_with(sensor_model)
    def get(self, id):
        '''Get all sensors used in a given platform configuration'''
        return Database.query_asjson("""
            select
               distinct s.*
            from li3ds.platform_config pf
            join li3ds.transfo_tree tt on tt.id = ANY(pf.transfo_trees)
            , lateral unnest(tt.transfos) as tid
            join li3ds.transfo t on t.id = tid
            join li3ds.referential r on r.id = t.source or r.id = t.target
            join li3ds.sensor s on s.id = r.sensor
            where pf.id = %s
            """, (id,))
