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
