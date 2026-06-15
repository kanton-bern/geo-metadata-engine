# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BGI Metadata Editor — a Django-based metadata management system for the WIS-BE project of Canton Bern. It manages geospatial metadata (layers, attributes, value tables).

## Development Setup

```bash
conda create -n bgi_metadata python=3.14
conda activate bgi_metadata
pip install -r requirements.txt
```

Configure a `.env` file (see `.env` for reference — required variables: `SECRET_KEY`, `DEBUG`, `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`). Optional (sensible defaults for local dev): `ALLOWED_HOSTS` (defaults to `127.0.0.1,localhost`) and `CSRF_TRUSTED_ORIGINS` (empty). The `ADFS_*` variables are only needed once ADFS authentication is activated (see `docs/adfs-oidc-setup.md`).

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver   # http://localhost:8000/
```

## Common Commands

```bash
python manage.py migrate                      # Apply database migrations
python manage.py makemigrations               # Create new migration files
python manage.py test                         # Run tests (editor/tests.py)
python manage.py test editor.tests.TestName   # Run a single test
python manage.py shell                        # Django interactive shell
docker build -t bgi_metadata .                # Build Docker image
```

## Code Style

Follow [PEP 8](https://peps.python.org/pep-0008/) for all Python code. Django's own [coding style](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/) applies for conventions specific to Django (models, views, admin). No automated formatter is enforced; consistency with the surrounding code is the guideline.

## Architecture

See [docs/scope_context.svg](docs/scope_context.svg) for the scope and context diagram.

### Project Layout

```
metadata/          # Django project config (settings, root URLs, wsgi)
editor/            # Single Django app containing all business logic
  models/          # One file per model (16 model files)
  views.py         # API endpoints + web map creation views
  admin.py         # Django admin with custom forms and inlines
  urls.py          # App-level URL routing
  templates/       # HTML templates
  migrations/      # Database schema history
  webMap.json      # Web map template
```

### Data Model Hierarchy

**Thema → Geopäckli → Ebene / Attribut / Wertetabelle**

- **Thema**: Top-level subject area (topic classification)
- **Geopäckli**: Core metadata container ("geo package") — owns Attribute and Wertetabellen; linked to a Thema
- **Ebene**: Geospatial layer definition (Raster/Vektor/Tabelle); linked to Geopäckli and Dienst; M2M with Attribut, Tags, Triggers, Views
- **Attribut**: Data field descriptor (name, type, constraints); belongs to Geopäckli; M2M with Ebene and Wertetabellen
- **Wertetabelle**: Enumeration/value table; belongs to Geopäckli; M2M with Attribut
- **Dienst**: Web service metadata (AWN/AGI owner, external flag)
- **Webmap**: Web map config (title, description, culture DE/FR)

Key design decision: Attribute belong to Geopäckli (not Ebene), so they survive layer deletion and can be reused across layers via M2M.

### Admin Interface

`editor/admin.py` has custom logic to filter the Attribut M2M field on Ebene forms to only show attributes belonging to the selected Geopäckli. This is done via a custom `EbeneAdminForm` with a filtered queryset.

### Deployment

CD pipeline via GitLab CI:
- Push to `dev` → deploys to `bgi-metadata-dev` Kubernetes namespace
- Push to `main` → deploys to `bgi-metadata-prod` Kubernetes namespace

Dockerfile uses a multi-stage Python 3.14-slim build; static files served by WhiteNoise.
