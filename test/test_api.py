#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from lids_api import create_app


@pytest.fixture
def app():
    app = create_app()
    return app


def test_get_projects(client):
    resp = client.get('/projects')
    assert resp.content_type == 'application/json'
    assert resp.status_code == 200
    assert 'name' in resp.json[0]
    assert 'timezone' in resp.json[0]
    assert 'extent' in resp.json[0]


def test_get_sessions(client):
    resp = client.get('/sessions')
    assert resp.content_type == 'application/json'
    assert resp.status_code == 200


def test_get_platforms(client):
    resp = client.get('/platforms')
    assert resp.content_type == 'application/json'
    assert resp.status_code == 200


def test_get_sensor_types(client):
    resp = client.get('/sensor_types')
    assert resp.content_type == 'application/json'
    assert resp.status_code == 200


def test_get_sensors(client):
    resp = client.get('/sensors')
    assert resp.content_type == 'application/json'
    assert resp.status_code == 200


def test_get_referentials(client):
    resp = client.get('/referentials')
    assert resp.content_type == 'application/json'
    assert resp.status_code == 200


def test_get_transfos(client):
    resp = client.get('/transfos')
    assert resp.content_type == 'application/json'
    assert resp.status_code == 200


def test_get_images(client):
    resp = client.get('/sessions/1/images')
    assert resp.content_type == 'application/json'
    assert resp.status_code == 200


def test_get_images_nosession(client):
    resp = client.get('/sessions/999999999/images')
    assert resp.content_type == 'application/json'
    assert resp.status_code == 404
