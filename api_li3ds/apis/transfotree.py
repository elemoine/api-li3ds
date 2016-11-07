# -*- coding: utf-8 -*-
from flask_restplus import fields

from api_li3ds.app import api, Resource
from api_li3ds.database import Database

nstft = api.namespace('transfotrees', description='transformation trees related operations')

transfotree_model_post = nstft.model(
    'Transformation tree Model Post',
    {
        'name': fields.String,
        'isdefault': fields.Boolean,
        'sensor_connections': fields.Boolean,
        'owner': fields.String,
        'transfos': fields.List(fields.Integer),
    })

transfotree_model = nstft.inherit(
    'Transformation tree Model',
    transfotree_model_post,
    {
        'id': fields.Integer
    })


@nstft.route('/', endpoint='transfotrees')
class TransfoTree(Resource):

    @nstft.marshal_with(transfotree_model)
    def get(self):
        '''List all transformation trees'''
        return Database.query_asjson("select * from li3ds.transfo_tree")

    @api.secure
    @nstft.expect(transfotree_model_post)
    @nstft.marshal_with(transfotree_model)
    @nstft.response(201, 'Transformation created')
    def post(self):
        '''Create a transformation between referentials'''
        return Database.query_asdict(
            """
            insert into li3ds.transfo_tree (name, isdefault, sensor_connections,
                                            owner, transfos)
            values (%(name)s,%(isdefault)s,%(sensor_connections)s,%(owner)s,%(transfos)s)
            returning *
            """,
            api.payload
        ), 201


@nstft.route('/<int:id>/', endpoint='transfotree')
@nstft.response(404, 'Transformation tree not found')
class OneTransfoTree(Resource):

    @nstft.marshal_with(transfotree_model)
    def get(self, id):
        '''Get one transformation given its identifier'''
        res = Database.query_asjson(
            "select * from li3ds.transfo_tree where id=%s", (id,)
        )
        if not res:
            nstft.abort(404, 'Transformation tree not found')
        return res

    @api.secure
    @nstft.response(410, 'Transformation deleted')
    def delete(self, id):
        '''Delete a transformation given its identifier'''
        res = Database.rowcount("delete from li3ds.transfo_tree where id=%s", (id,))
        if not res:
            nstft.abort(404, 'Transformation tree not found')
        return '', 410
