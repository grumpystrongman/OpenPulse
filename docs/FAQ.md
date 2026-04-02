# FAQ

## Is this production-ready?
The reference stack is locally production-like and includes observability, replay, quality scoring, and governance gates.

## Can I query with SQL directly?
Yes, ClickHouse is exposed on port 8123 and includes silver/gold tables and views.

## Do you support real manufacturer credentials?
Yes for adapter patterns. The demo includes realistic synthetic streams when live credentials are unavailable.

## How are extensions handled?
Controlled namespace + schema versioning, without breaking open core contracts.
