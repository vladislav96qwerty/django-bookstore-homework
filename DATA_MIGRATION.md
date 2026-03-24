# Data Migration: SQLite to PostgreSQL

This guide explains how to safely migrate existing data from SQLite to PostgreSQL in the current Docker-based project.

## 1) Dump data from SQLite

Create a JSON backup from your current SQLite database.  
`contenttypes` and `auth.Permission` are excluded to avoid permission/content type conflicts during import.

```bash
python manage.py dumpdata --exclude contenttypes --exclude auth.Permission --indent 2 > data.json
```

## 2) Build Docker containers

Build all required images before starting services.

```bash
docker compose build
```

## 3) Start PostgreSQL and Redis services

Start only infrastructure services first (database and cache).

```bash
docker compose up -d db redis
```

Check that services are healthy:

```bash
docker compose ps
```

## 4) Apply migrations on PostgreSQL

Create database schema in PostgreSQL using Django migrations.

```bash
docker compose run --rm web python manage.py migrate
```

## 5) Load dumped data into PostgreSQL

Import the previously created JSON dump.

```bash
docker compose run --rm web python manage.py loaddata data.json
```

## 6) Start full application

Run the complete stack (web + db + redis).

```bash
docker compose up --build
```

## 7) Verify migrated data

Run a quick Django shell check to confirm key record counts.

```bash
docker compose run --rm web python manage.py shell -c "from django.contrib.auth.models import User; from shop.models import Book, Category; print('Users:', User.objects.count(), 'Categories:', Category.objects.count(), 'Books:', Book.objects.count())"
```

## Notes

- Do **not** delete `db.sqlite3` until you verify PostgreSQL data is correct.
- Keep `data.json` as a migration backup file.
- Running `loaddata` multiple times against the same PostgreSQL database may cause duplicate records or constraint conflicts.

## Troubleshooting

### 1) `connection refused` / database is not ready

PostgreSQL container may still be starting.

```bash
docker compose ps
docker compose logs db
```

Wait for healthy status, then re-run migration/load commands.

### 2) `could not translate host name "db"`

Command was likely run outside Docker network context.  
Use `docker compose run --rm web ...` for Django commands that must connect to `db`.

```bash
docker compose run --rm web python manage.py migrate
```

### 3) `duplicate key value violates unique constraint` during `loaddata`

Data was already loaded (or partially loaded) before.

- Preferred fix: load data once into a fresh PostgreSQL schema.
- If needed, recreate PostgreSQL volume intentionally and re-run migration/import workflow.

### 4) `ImproperlyConfigured` / missing env variables

Ensure `.env` exists and contains DB credentials used by Docker Compose.

```bash
docker compose config
```

Validate that `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` are present.

