from fastapi.testclient import TestClient

from web.main import app

test_app = TestClient(app)


def test_root():
    response = test_app.get("/", params={"a": 1, "b": 123})
    assert response.json() == {"a": 1, "b": "123"}
