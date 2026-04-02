# Conformance Kit

Run:
```powershell
python -m pytest tests/contract tests/integration tests/e2e
```

Conformance assertions:
- Envelope schema validity.
- Canonical observation schema validity.
- Provenance linkage for each normalized observation.
- Unit normalization + original unit preservation.
- Idempotency conflict behavior.
- Replay queue behavior for malformed payloads.
