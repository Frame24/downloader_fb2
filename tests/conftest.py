import pytest
import requests


class DummyResp:
    def __init__(self, data):
        self._data = data
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return {"data": self._data}


@pytest.fixture(autouse=True)
def no_net(monkeypatch):
    """Запрещаем реальные HTTP-запросы."""
    monkeypatch.setattr(
        requests,
        "get",
        lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("HTTP-запросы не разрешены в тестах")
        ),
    )
