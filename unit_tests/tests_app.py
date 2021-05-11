import json
from pytest import mark


# @mark.unit_tests
# @mark.ping
# def test_ping(test_app):
#     client = test_app.test_client()
#     resp = client.get('/ping')
#     data = json.loads(resp.data.decode())
#     assert resp.status_code == 200
#     assert 'Successful Health check.' in data['message']


@mark.unit_tests
@mark.execution_parameters
def test_execution_parameters(test_app):
    client = test_app.test_client()
    resp = client.get('/execution-parameters')
    data = json.loads(resp.data.decode())
    assert resp.status_code == 200
    assert data['MaxConcurrentTransforms'] == 1
    assert 'MULTI_RECORD' in data['BatchStrategy']


@mark.unit_tests
@mark.invocations
@mark.invocations_success
def test_api_success(test_app):
    client = test_app.test_client()
    with open(f"input_file/input_25.csv", 'r', encoding='utf-8') as aft_file:
        response = client.post('/invocations',
                               headers={"Content-Type": "text/plain",
                                        "Tracker-Id": "unit_tests",
                                        "log-level": "debug"},
                               data=aft_file.read().encode('utf-8'))
    assert response.status_code == 200


@mark.unit_tests
@mark.invocations
@mark.invocations_fail
def test_api_not_plain(test_app):
    client = test_app.test_client()
    with open(f"input_file/input_25.csv", 'r', encoding='utf-8') as aft_file:
        response = client.post('/invocations',
                               headers={"Content-Type": "application/json",
                                        "Tracker-Id": "unit_tests",
                                        "log-level": "debug"},
                               data=aft_file.read().encode('utf-8'))
    data = response.data.decode()
    assert response.status_code == 415
    assert "This predictor accepts only plain text" in data
