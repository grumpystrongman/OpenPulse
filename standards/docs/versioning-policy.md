# Versioning and Compatibility Policy

- Schema package: `openpulse-standard`.
- Version format: semantic versioning.
- Compatibility guarantees:
  - Minor releases are backward-compatible for producers and consumers.
  - Major releases require migration tooling and dual-read period.
- Deprecation policy:
  - Minimum two minor versions before field removal.
  - Deprecation warnings in release notes and API headers.
- Migration expectations:
  - SQL migrations for warehouse changes.
  - JSON schema migration notes and sample transforms.
