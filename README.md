# GnuCash Dashboard

Dashboard Streamlit pour explorer un livre GnuCash avec une couche “analytics”.

- Sources supportées : base GnuCash PostgreSQL (via SQLAlchemy) et/ou livre PieCash (optionnel).
- Couche analytics : miroir (tables) et/ou vues SQL pré-calculées.
- UI : Streamlit avec pages `Dashboard`, `Accounts`, `Flux de trésorerie`, `Budget`, `Diagnostics`.

## Architecture (hexagonale)

```
adapters (CLI/Streamlit) -> application (use cases) -> ports -> infrastructure (DB/PieCash)
```

- `src/application/use_cases/` : orchestration (sync, lecture analytics, comparaisons).
- `src/infrastructure/` : accès DB (engines), backends GnuCash (SQLAlchemy / analytics / piecash).
- `src/adapters/` : CLIs + UI Streamlit (sans logique métier).

## Prérequis

- Python `>=3.11,<3.12` + `uv` installé.
- PostgreSQL accessible pour :
  - `GNUCASH_DB_URL` : la base GnuCash (ou schéma) source,
  - `ANALYTICS_DB_URL` : la base/schéma analytics (peut être la même DB).

## Installation

```bash
uv sync
```

## Configuration (ENV / .env)

Le projet charge automatiquement un fichier `.env` s’il existe (via `python-dotenv`).

Variables principales :

- `GNUCASH_DB_URL` : URL SQLAlchemy Postgres (ex: `postgresql://user:pass@host:5432/gnucash`)
- `ANALYTICS_DB_URL` : URL SQLAlchemy Postgres (ex: `postgresql://user:pass@host:5432/gnucash_analytics`)
- `GNUCASH_BACKEND` : `sqlalchemy` (défaut), `analytics`, ou `piecash`
- `ANALYTICS_READ_MODE` : `tables` (défaut) ou `views`
- `PIECASH_FILE` (optionnel) : chemin `.gnucash` ou URI (ex: `postgresql://...`) pour PieCash

## Lancer l’app Streamlit

```bash
uv run python -m streamlit run src/adapters/interface/streamlit/app.py
```

## CLIs (sync / ops)

- Tester la connectivité DB :
  - `uv run python -m src.adapters.test_db_connection`
- Synchroniser les tables “brutes” GnuCash vers l’analytics :
  - `uv run python -m src.adapters.sync_gnucash_analytics_cli`
- Synchroniser uniquement l’arbre des comptes (use case dédié) :
  - `uv run python -m src.adapters.sync_accounts_cli`
- Comparer SQLAlchemy vs PieCash (sanity check) :
  - `uv run python -m src.adapters.compare_backends_cli`
  - variables optionnelles : `SANITY_START_DATE=YYYY-MM-DD`, `SANITY_END_DATE=YYYY-MM-DD`, `SANITY_CURRENCY=EUR`

## Mode “analytics views” (optionnel)

Pour lire des vues SQL pré-calculées plutôt que des tables miroir, définir :

```
ANALYTICS_READ_MODE=views
```

Vues attendues côté `ANALYTICS_DB_URL` :

- `vw_currency_lookup(guid, mnemonic, namespace)`
- `vw_net_worth_balances(account_type, commodity_guid, mnemonic, namespace, balance, post_date)`
- `vw_asset_category_balances(account_type, commodity_guid, mnemonic, namespace, actif_category, actif_subcategory, balance, actif_root_name, post_date)`
- `vw_latest_prices(commodity_guid, currency_guid, value_num, value_denom, date)`

## PieCash (optionnel)

Installer l’extra :

```bash
uv sync --extra piecash
```

Puis configurer :

- `GNUCASH_BACKEND=piecash`
- `PIECASH_FILE=/chemin/vers/book.gnucash` (ou `PIECASH_FILE=postgresql://user:pass@host/dbname`)

## Tests

```bash
uv run pytest
```
