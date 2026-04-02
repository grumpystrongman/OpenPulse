import importlib.util
from pathlib import Path


class DummyProducer:
    def __init__(self) -> None:
        self.records = []

    def produce(self, topic, value):
        self.records.append((topic, value))

    def flush(self, _timeout):
        return None


def _load_replay_module():
    path = Path("scripts/replay_failed.py")
    spec = importlib.util.spec_from_file_location("replay_failed", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def test_replay_failed_records(monkeypatch) -> None:
    module = _load_replay_module()
    producer = DummyProducer()
    monkeypatch.setattr(module, "get_producer", lambda: producer)
    monkeypatch.setattr(
        module,
        "query",
        lambda _sql: [
            {"failed_id": "f1", "envelope_json": '{"manufacturer":"fitbit"}'},
            {"failed_id": "f2", "envelope_json": '{"manufacturer":"dexcom"}'},
        ],
    )
    updates = []
    monkeypatch.setattr(module, "execute", lambda sql: updates.append(sql))

    module.main(limit=2)
    assert len(producer.records) == 2
    assert len(updates) == 2
