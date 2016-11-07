# -*- coding: utf-8 -*-
from flask_restplus import fields

from api_li3ds.app import api, Resource
from api_li3ds.database import Database


nssensor = api.namespace('sensors', description='sensors related operations')


sensor_model_post = nssensor.model(
    'Sensor Model Post',
    {
        'serial_number': fields.String,
        'short_name': fields.String,
        'brand': fields.String,
        'model': fields.String,
        'description': fields.String,
        'type': fields.String(required=True),
        'specifications': fields.Raw,
    })


sensor_model = nssensor.inherit(
    'Sensor Model',
    sensor_model_post,
    {
        'id': fields.Integer
    })


@nssensor.route('/', endpoint='sensors')
class Sensors(Resource):

    @nssensor.marshal_with(sensor_model)
    def get(self):
        '''List sensors'''
        return Database.query_asjson("select * from li3ds.sensor")

    @api.secure
    @nssensor.expect(sensor_model_post)
    @nssensor.marshal_with(sensor_model)
    @nssensor.response(201, 'Sensor created')
    def post(self):
        '''Create a sensor'''
        return Database.query_asdict(
            """
            insert into li3ds.sensor (serial_number, short_name, brand,
                                      model, description, specifications, type)
            values (%(serial_number)s, %(short_name)s, %(brand)s, %(model)s,
                    %(description)s, %(specifications)s, %(type)s)
            returning *
            """,
            api.payload
        ), 201


@nssensor.route('/<int:id>/', endpoint='sensor')
@nssensor.response(404, 'Sensor not found')
class OneSensor(Resource):

    @nssensor.marshal_with(sensor_model)
    def get(self, id):
        '''Get one sensor given its identifier'''
        res = Database.query_asjson(
            "select * from li3ds.sensor where id=%s", (id,)
        )
        if not res:
            nssensor.abort(404, 'sensor not found')
        return res

    @api.secure
    @nssensor.response(410, 'Sensor deleted')
    def delete(self, id):
        '''Delete a sensor given its identifier'''
        res = Database.rowcount("delete from li3ds.sensor where id=%s", (id,))
        if not res:
            nssensor.abort(404, 'Sensor not found')
        return '', 410


@nssensor.route('/types/', endpoint='sensor_types')
class Sensor_types(Resource):

    def get(self):
        '''Sensor type list'''
        return Database.query_aslist(
            '''select unnest(enum_range(enum_first(null::li3ds.sensor_type),
            null::li3ds.sensor_type))'''
        )
