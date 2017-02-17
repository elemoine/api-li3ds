#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import url_for


def test_get_projects(client):
    resp = client.get(url_for('projects'))
    assert resp.content_type == 'application/json'
    assert resp.status_code == 200


def test_project(client):
    client.post(url_for('project', name='Toulouse'))
    resp = client.get(url_for('project', name='Toulouse'))
    assert resp.content_type == 'application/json'
    assert resp.status_code == 200
