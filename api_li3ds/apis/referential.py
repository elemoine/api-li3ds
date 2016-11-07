# -*- coding: utf-8 -*-
from flask_restplus import fields

from api_li3ds.app import api, Resource
from api_li3ds.database import Database

nsrf = api.namespace('referentials', description='referentials related operations')

referential_model_post = nsrf.model(
    'Referential Model Post',
    {
        'name': fields.String,
        'description': fields.String,
        'srid': fields.Integer,
        'root': fields.Boolean,
        'sensor': fields.Integer,
    })

referential_model = nsrf.inherit(
    'Referential Model',
    referential_model_post,
    {
        'id': fields.Integer
    })


transfo_model = nsrf.model(
    'Transfo Model',
    {
        'id': fields.Integer,
        'source': fields.Integer,
        'target': fields.Integer,
        'transfo_type': fields.Integer,
        'description': fields.String,
        'parameters': fields.Raw,
        'tdate': fields.DateTime(dt_format='iso8601'),
        'validity_start': fields.DateTime(dt_format='iso8601', default=None),
        'validity_end': fields.DateTime(dt_format='iso8601', default=None),
    })


@nsrf.route('/', endpoint='referentials')
class Referential(Resource):

    @nsrf.marshal_with(referential_model)
    def get(self):
        '''List Referentials'''
        return Database.query_asjson("select * from li3ds.referential")

    @api.secure
    @nsrf.expect(referential_model_post)
    @nsrf.marshal_with(referential_model)
    @nsrf.response(201, 'Platform created')
    def post(self):
        '''Create a referential'''
        return Database.query_asdict(
            "insert into li3ds.referential (name, description, srid, root, sensor) "
            "values (%(name)s, %(description)s, %(srid)s, %(root)s, %(sensor)s) "
            "returning *",
            api.payload
        ), 201


@nsrf.route('/<int:id>', endpoint='referential')
@nsrf.response(404, 'Referential not found')
class OneReferential(Resource):

    @nsrf.marshal_with(referential_model)
    def get(self, id):
        '''Get one referential given its identifier'''
        res = Database.query_asjson(
            "select * from li3ds.referential where id=%s", (id,)
        )
        if not res:
            nsrf.abort(404, 'Referential not found')
        return res

    @api.secure
    @nsrf.response(410, 'Referential deleted')
    def delete(self, id):
        '''Delete a referential given its identifier'''
        res = Database.rowcount("delete from li3ds.referential where id=%s", (id,))
        if not res:
            nsrf.abort(404, 'referential not found')
        return '', 410
