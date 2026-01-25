# Deployment Configuration

## What Exists in the Repo

- No `Dockerfile` / `docker-compose.*`
- No `.github/workflows/*`
- No Kubernetes / Helm / Terraform / Pulumi detected

## Operational Requirements

- A PostgreSQL instance accessible from where Streamlit/CLIs run.
- Environment variables set (or `.env` present for local usage).

## Analytics “Views” Mode

If `ANALYTICS_READ_MODE=views`, ensure these views exist on `ANALYTICS_DB_URL` (see `README.md`):

- `vw_currency_lookup`
- `vw_net_worth_balances`
- `vw_asset_category_balances`
- `vw_latest_prices`

