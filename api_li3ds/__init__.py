# -*- coding: utf-8 -*-
import io
import os
import sys
import logging
from pathlib import Path

from flask import Flask
from yaml import load as yload

from api_li3ds.app import api, init_apis
from api_li3ds.database import Database

__version__ = '0.1.dev0'


LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}


def load_yaml_config(filename):
    """
    Open Yaml file, load content for flask config and returns it as a python dict
    """
    content = io.open(filename, 'r').read()
    return yload(content).get('flask', {})


def create_app():
    """
    Creates application.

    :returns: flask application instance
    """
    app = Flask(__name__)
    cfgfile = os.environ.get('API_LI3DS_SETTINGS')
    if cfgfile:
        app.config.update(load_yaml_config(cfgfile))
    else:
        try:
            cfgfile = (Path(__file__).parent.parent / 'conf' / 'api_li3ds.yml').resolve()
        except FileNotFoundError:
            print(Path(__file__).parent.parent / 'conf' / 'api_li3ds.yml')
            app.logger.warning('no config file found !!')
            sys.exit(1)
    app.config.update(load_yaml_config(str(cfgfile)))

    # setting log level
    if app.config['DEBUG']:
        app.logger.setLevel(LOG_LEVELS['debug'])
    else:
        app.logger.setLevel(LOG_LEVELS['info'])

    app.logger.debug('loading config from {}'.format(cfgfile))

    # load extensions
    # be carefull to load apis before blueprint !
    init_apis()
    api.init_app(app)
    Database.init_app(app)
    return app
