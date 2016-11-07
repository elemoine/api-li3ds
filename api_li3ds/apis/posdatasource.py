# -*- coding: utf-8 -*-
from flask_restplus import fields

from api_li3ds.app import api, Resource
from api_li3ds.database import Database


nspds = api.namespace('posdatasources', description='positional datasources related operations')

posdatasource_model_post = nspds.model('Posdatasource Model Post', {
    'uri': fields.String,
    'referential': fields.Integer(required=True),
    'version': fields.Integer,
    'session': fields.Integer(required=True)
})


posdatasource_model = nspds.inherit('Posdatasource Model', posdatasource_model_post, {
    'id': fields.Integer,
})

posprocessing_model_post = nspds.model('PosProcessing Model Post', {
    'launched': fields.DateTime(dt_format='iso8601', default=None),
    'tool': fields.String(required=True),
    'description': fields.String,
    'source': fields.Integer(required=True),
})

posprocessing_model = nspds.inherit('PosProcessing Model', posprocessing_model_post, {
    'id': fields.Integer,
    'target': fields.Integer(required=True)
})


@nspds.route('/', endpoint='posdatasources')
class PosDatasources(Resource):

    @nspds.marshal_with(posdatasource_model)
    def get(self):
        '''Get all datasources'''
        return Database.query_asjson("select * from li3ds.posdatasource")

    @api.secure
    @nspds.expect(posdatasource_model_post)
    @nspds.marshal_with(posdatasource_model)
    @nspds.response(201, 'PosDatasource created')
    def post(self):
        '''Create a datasource'''
        return Database.query_asdict(
            "insert into li3ds.posdatasource (referential, session, uri) "
            "values (%(referential)s, %(session)s, %(uri)s) "
            "returning *",
            api.payload
        ), 201


@nspds.route('/<int:id>/', endpoint='posdatasource')
@nspds.response(404, 'PosDatasource not found')
class OnePosDatasource(Resource):

    @nspds.marshal_with(posdatasource_model)
    def get(self, id):
        '''Get one datasource given its identifier'''
        res = Database.query_asjson(
            "select * from li3ds.posdatasource where id=%s", (id,)
        )
        if not res:
            nspds.abort(404, 'PosDatasource not found')
        return res

    @api.secure
    @nspds.response(410, 'PosDatasource deleted')
    def delete(self, id):
        '''Delete a datasource given its identifier'''
        res = Database.rowcount("delete from li3ds.posdatasource where id=%s", (id,))
        if not res:
            nspds.abort(404, 'PosDatasource not found')
        return '', 410


@nspds.route('/<int:id>/posprocessing/', endpoint='posdatasource_posprocessing')
@nspds.param('id', 'The datasource identifier')
@nspds.response(404, 'PosDatasource not found')
class PosProcessing(Resource):

    @nspds.marshal_with(posprocessing_model)
    def get(self, id):
        '''Get the posprocessing tool used to generate this datasource'''
        res = Database.query_asjson(
            "select * from li3ds.posdatasource where id=%s", (id,)
        )
        if not res:
            nspds.abort(404, 'PosDatasource not found')

        return Database.query_asjson(
            " select p.* from li3ds.posprocessing p"
            " join li3ds.posdatasource s on s.id = p.target where s.id=%s",
            (id,)
        )

    @api.secure
    @nspds.expect(posprocessing_model_post)
    @nspds.marshal_with(posprocessing_model)
    @nspds.response(201, 'PosDatasource created')
    def post(self, id):
        '''Add a new posprocessing tool that has generated the given datasource'''
        return Database.query_asdict(
            "insert into li3ds.posprocessing (launched, tool, description, source, target) "
            "values (%(launched)s, %(tool)s, %(description)s, %(source)s, {}) "
            "returning *".format(id),
            api.payload
        ), 201


@nspds.route('/posprocessing/<int:id>/', endpoint='posprocessing')
@nspds.param('id', 'The PosProcessing identifier')
@nspds.response(404, 'PosProcessing not found')
class OneProcessing(Resource):

    @nspds.marshal_with(posprocessing_model)
    def get(self, id):
        '''Get posprocessing tool given its id'''
        return Database.query_asjson(
            " select * from li3ds.posprocessing where id = %s", (id,)
        )

    @api.secure
    @nspds.response(410, 'PosProcessing deleted')
    def delete(self, id):
        '''Delete a posprocessing entry'''
        res = Database.rowcount("delete from li3ds.posprocessing where id=%s", (id,))
        if not res:
            nspds.abort(404, 'PosProcessing not found')
        return '', 410
