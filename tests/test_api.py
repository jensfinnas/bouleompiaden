import os

import pytest

import api

@pytest.fixture
def client():
    api.app.config['TESTING'] = True
    client = api.app.test_client()

    yield client

    os.close(db_fd)
    os.unlink(api.app.config['DATABASE'])


def test_simulate_game(client):
    """Start with a blank database."""
    p1 = "Gabriel Nordenankar"
    p2 = "Erik Nordenankar"
    r = client.get('/simulate/{}/vs/{}'.format(p1, p2))
    assert r.status_code == 200
