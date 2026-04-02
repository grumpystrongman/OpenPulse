# Extension Registry Rules

- Namespace format: `openpulse.ext.<vendor_or_domain>`.
- Every extension key must have:
  - owner
  - semantic meaning
  - value type
  - stability state (`experimental`, `stable`, `deprecated`)
- Vendor extension fields cannot override canonical metric meaning.
- Vendor extension payload must include a `schema_version`.
