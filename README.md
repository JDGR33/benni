# benni

Scrapes exchange rates from the Banco Central de Venezuela (BCV) website and stores them in a PostgreSQL table.

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
DB_HOST=localhost
DB_PORT=5432
```

`DB_HOST` and `DB_PORT` are optional (defaults are shown above).

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

## Notes

- If BCV changes the HTML ids used for currencies, extraction may return `Not found`.
- Current script stores rate values as text (`VARCHAR`).
