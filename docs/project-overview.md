# Project Overview

## Purpose

Streamlit dashboard to explore a GnuCash book with an “analytics” layer. Supports reading GnuCash data from:

- a PostgreSQL GnuCash DB/schema (via SQLAlchemy),
- optional PieCash book (local file or Postgres URI),
- an analytics schema populated by sync jobs and/or read via SQL views.

## Quick Facts

- **Repo type:** monolith
- **Primary language:** Python
- **UI:** Streamlit
- **DB:** PostgreSQL
- **Architecture:** ports & adapters (hexagonal)

## Where To Start

- Master index: `docs/index.md`
- If you’re planning new features (brownfield PRD): use the index as the primary context entry point.

