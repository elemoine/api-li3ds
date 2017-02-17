import pytest

from api_li3ds import create_app


@pytest.fixture
def app():
    app = create_app()
    return app
