#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import url_for


def test_get_projects(client):
    resp = client.get(url_for('projects'))
    assert resp.content_type == 'application/json'
    assert resp.status_code == 200


def test_get_sessions(client):
    resp = client.get(url_for('sessions'))
    assert resp.content_type == 'application/json'
    assert resp.status_code == 200


def test_get_platforms(client):
    resp = client.get(url_for('platforms'))
    assert resp.content_type == 'application/json'
    assert resp.status_code == 200


def test_get_sensor_types(client):
    resp = client.get(url_for('sensor_types'))
    assert resp.content_type == 'application/json'
    assert resp.status_code == 200


def test_get_sensors(client):
    resp = client.get(url_for('sensors'))
    assert resp.content_type == 'application/json'
    assert resp.status_code == 200


def test_get_referentials(client):
    resp = client.get(url_for('referentials'))
    assert resp.content_type == 'application/json'
    assert resp.status_code == 200


def test_get_transfos(client):
    resp = client.get(url_for('transfos'))
    assert resp.content_type == 'application/json'
    assert resp.status_code == 200
