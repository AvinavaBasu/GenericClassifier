from container.wsgi import app
from pytest import fixture


@fixture(scope='session')
def test_app():
    with app.app_context():
        yield app
