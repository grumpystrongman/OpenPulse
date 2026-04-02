# Security Notes (Non-Legal Advice)

- Local secrets are managed through `.env` and environment variables.
- In production use a dedicated secret manager and rotate keys regularly.
- Enforce TLS for all service and external API traffic.
- Use scoped OAuth tokens and short-lived access tokens.
- Enable audit logging for ingest/export/governance override paths.
