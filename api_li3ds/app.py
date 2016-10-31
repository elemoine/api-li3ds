# -*- coding: utf-8 -*-
from flask_restplus import Api, Resource as OrigResource

from api_li3ds.database import pgexceptions

HEADER_API_KEY = 'X-API-KEY'


class Resource(OrigResource):
    # add a postgresql exception decorator for all api methods
    method_decorators = [pgexceptions]


api = Api(
    version='1.0', title='Large Input 3D System API',
    description='API for accessing LI3DS metadata',
    validate=True,
    authorizations={
        'apikey': {
            'type': 'apiKey',
            'in': 'header',
            'name': HEADER_API_KEY
        }
    }
)


def init_apis():
    from api_li3ds.apis.project import nsproject
    from api_li3ds.apis.session import nssession
    from api_li3ds.apis.platform import nspfm
    from api_li3ds.apis.itowns import nsitowns
    from api_li3ds.apis.datasource import nsds
    from api_li3ds.apis.posdatasource import nspds
    from api_li3ds.database import pgexceptions
