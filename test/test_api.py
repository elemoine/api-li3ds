#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from lids_api import create_app


@pytest.fixture
def app():
    app = create_app()
    return app


def test_get_project_list(client):
    resp = client.get('/projects')
    assert resp.content_type == 'application/json'
    assert 'name' in resp.json[0]
    assert 'timezone' in resp.json[0]
    assert 'extent' in resp.json[0]
