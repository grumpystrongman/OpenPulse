# ADR-0002: Service Stack

Date: 2026-04-02

## Decision
Use Python/FastAPI for API and orchestration services.

## Rationale
- Fast iteration speed for multiple domain services.
- Strong typing via Pydantic and OpenAPI generation.
- Mature ecosystem for data and healthcare integration.

## Consequences
- Uniform language across services lowers maintenance cost.
- CPU-heavy processing can later be moved to Rust/Go workers if required.
