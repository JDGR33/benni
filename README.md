# benni

Scrapes exchange rates from the Banco Central de Venezuela (BCV) website and stores them in a PostgreSQL table.

This repo is ready to run as Docker containers:
- `postgres` service for storage
- `scraper` service with internal cron scheduler (runs 3 times/day in UTC)

## What it does

- Fetches `https://www.bcv.org.ve/`
- Extracts rates for these currencies by page element id:
	- `dolar`
	- `euro`
	- `yuan`
	- `lira`
	- `rublo`
- Inserts the values into a PostgreSQL table called `currency_rates`
- Records a `scraped_at` timestamp for each run

## Requirements

- Python 3.9+
- PostgreSQL
- Network access to `https://www.bcv.org.ve/`

For containerized run:
- Docker Engine
- Docker Compose (v2)

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Environment variables

Create a `.env` file in the project root with:

```env
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password

# Optional overrides (defaults shown)
DB_HOST=localhost
DB_PORT=5432

# Optional retry tuning
FETCH_RETRIES=3
FETCH_RETRY_DELAY=5
DB_RETRIES=5
DB_RETRY_DELAY=5
ALLOW_INSECURE_SSL_FALLBACK=true
```

`DB_HOST` and `DB_PORT` are optional (defaults are shown above).

For Docker Compose, copy `.env.example` to `.env` and adjust values:

```bash
cp .env.example .env
```

## Database table

The script creates this table automatically if it does not exist:

- Table: `currency_rates`
- Columns:
	- `id SERIAL PRIMARY KEY`
	- `currency VARCHAR(20) NOT NULL`
	- `rate VARCHAR(50)`
	- `scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`

## Run

```bash
python main.py
```

The script logs fetched values and inserts one row per currency for each execution.

## Run with Docker (recommended)

Build and start:

```bash
docker compose up -d --build
```

Stop:

```bash
docker compose down
```

Stop and remove DB data volume:

```bash
docker compose down -v
```

### Scheduler details

- Schedule: `0 0,8,16 * * *`
- Timezone: UTC
- Runs inside the `scraper` container using cron

### How the scheduler files work

The scheduler is split across three files that run in sequence:

1. `entrypoint.sh` (container startup)
2. `benni-cron` (cron schedule definition)
3. `cronjob.sh` (job wrapper that runs Python)

Execution flow:

1. The container starts and runs `entrypoint.sh`.
2. `entrypoint.sh` sets `TZ` (defaults to `UTC`) and writes all current environment variables into `/etc/profile.d/container_env.sh` as `export ...` lines.
3. `entrypoint.sh` installs the crontab from `/etc/cron.d/benni-cron` and starts cron in foreground with `exec cron -f`.
4. Cron reads `benni-cron` and triggers `/app/cronjob.sh` at `0 0,8,16 * * *`.
5. `cronjob.sh` sources `/etc/profile.d/container_env.sh`, changes to `/app`, and runs `python main.py`.

Important command behavior:

- In `benni-cron`, `>> /proc/1/fd/1 2>> /proc/1/fd/2` sends job output to the container's main stdout/stderr so logs appear in `docker logs`.
- `set -e` in shell scripts makes them fail fast if any command returns a non-zero exit code.
- Using a saved env file is necessary because cron jobs do not inherit the full interactive/container environment by default.

### Logs and verification

Scraper logs:

```bash
docker logs -f benni-scraper
```

Postgres logs:

```bash
docker logs -f benni-postgres
```

Check inserted rows:

```bash
docker exec -it benni-postgres psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT currency, rate, scraped_at FROM currency_rates ORDER BY scraped_at DESC LIMIT 20;"
```

## Notes

- If BCV changes the HTML ids used for currencies, extraction may return `Not found`.
- Current script stores rate values as text (`VARCHAR`).
- `docker-compose.yml` sets `DB_HOST=postgres` for the scraper service automatically.
- `ALLOW_INSECURE_SSL_FALLBACK=true` enables a fallback request with `verify=False` when BCV SSL verification fails.


# Docker Lessons

## Main Concepts

- `Dockerfile` defines how to build the `scraper` image only (Python runtime, dependencies, cron setup, entrypoint).
- `docker-compose.yml` defines the full app stack and how services run together (`postgres` + `scraper`).
- The database is not built in your `Dockerfile` because it uses the official `postgres:16` image as a separate service.
- Service-to-service communication happens through the Compose network; `DB_HOST=postgres` works because `postgres` is the service name.
- Persistence is handled with the named volume `benni_postgres_data`, so DB data survives container restarts and recreations.
- `depends_on` with `condition: service_healthy` helps ensure `scraper` starts after Postgres is ready.
- `docker exec -it` is useful for interactive troubleshooting inside running containers (for example with `psql`).

## Valuable Docker Commands For This Project

Start and build containers:

```bash
docker compose up -d --build
```

Check running services:

```bash
docker compose ps
```

View scraper logs:

```bash
docker logs -f benni-scraper
```

View database logs:

```bash
docker logs -f benni-postgres
```

Open interactive PostgreSQL shell:

```bash
docker exec -it benni-postgres psql -U "$DB_USER" -d "$DB_NAME"
```

Run one SQL query without entering shell:

```bash
docker exec -it benni-postgres psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT currency, rate, scraped_at FROM currency_rates ORDER BY scraped_at DESC LIMIT 20;"
```

List tables in the connected database:

```bash
docker exec -it benni-postgres psql -U "$DB_USER" -d "$DB_NAME" -c "\dt"
```

Count inserted rows:

```bash
docker exec -it benni-postgres psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT COUNT(*) FROM currency_rates;"
```

Stop containers:

```bash
docker compose down
```

Stop containers and remove DB volume (deletes DB data):

```bash
docker compose down -v
```