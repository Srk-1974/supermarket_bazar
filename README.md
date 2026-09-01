Supermarket/Bazaar DB - Quick Start

Files added:
- db/schema_postgres.sql  : Full PostgreSQL schema DDL
- db/seed_sample.sql     : Minimal seed data for quick verification
- .env.example           : DB config template
- requirements.txt       : Python deps for connection test
- scripts/test_connection.py : Simple connection test script

Quick local run using Docker (Postgres):

1) Start Postgres with Docker:

```bash
docker run --name supermarket-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=supermarketdb -p 5432:5432 -d postgres:15
```

2) Apply schema (use `psql` or a GUI client):

```bash
# with psql (on host)
psql -h localhost -p 5432 -U postgres -d supermarketdb -f db/schema_postgres.sql

# or inside container
docker exec -i supermarket-db psql -U postgres -d supermarketdb -f /tmp/schema_postgres.sql
# (you'd need to copy file into container first)
```

3) Seed sample data:

```bash
psql -h localhost -p 5432 -U postgres -d supermarketdb -f db/seed_sample.sql
```

4) Test connection using Python script (create a `.env` from `.env.example` and set credentials):

```bash
python -m pip install -r requirements.txt
cp .env.example .env
# edit .env to match your DB credentials if needed
python scripts/test_connection.py
```

Notes & next steps:
- If you provide a DB link (connection string), I can run the test script against it and optionally apply schema/seed automatically.
- I can also produce MySQL or SQL Server variants of the DDL if needed.
