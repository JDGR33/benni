# Add psycopg2 for PostgreSQL integration
import requests
from bs4 import BeautifulSoup
import logging
import certifi
# PostgreSQL and dotenv integration
import psycopg2
from dotenv import load_dotenv
import os
from datetime import datetime

# TODO: Take a look at how to solve the ssl problem
# TODO: Data base connection
def connect_postgres(dbname, user, password, host='localhost', port=5432):
    """Connect to PostgreSQL and return connection."""
    try:
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        logging.info("Connected to PostgreSQL database.")
        return conn
    except Exception as e:
        logging.error(f"PostgreSQL connection error: {e}")
        return None

def create_table_if_not_exists(conn):
    """Create currency_rates table if it doesn't exist."""
    query = '''
    CREATE TABLE IF NOT EXISTS currency_rates (
        id SERIAL PRIMARY KEY,
        currency VARCHAR(20) NOT NULL,
        rate VARCHAR(50),
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    '''
    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()

def insert_currency_data(conn, data, scraped_at):
    """Insert currency data into the table."""
    with conn.cursor() as cur:
        for currency, rate in data:
            cur.execute(
                "INSERT INTO currency_rates (currency, rate, scraped_at) VALUES (%s, %s, %s)",
                (currency, rate, scraped_at)
            )
        conn.commit()

# Configure logging
logging.basicConfig(level=logging.INFO)

def extract_strong_text_by_id(soup, div_id):
    """Return text inside <strong> tag within a div of given id."""
    div = soup.find('div', id=div_id)
    if div:
        strong_tag = div.find('strong')
        if strong_tag:
            return strong_tag.get_text(strip=True)
    return None

def fetch_html(url):
    """Fetch HTML content from a URL."""
    try:
        response = requests.get(url, verify=certifi.where())
        response.raise_for_status()
        logging.info(f"Fetched content from {url}")
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching {url}: {e}")
        return None

def parse_html(html):
    """Parse HTML content and return BeautifulSoup object."""
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        return soup
    else:
        logging.error("No HTML to parse.")
        return None

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    url = "https://www.bcv.org.ve/"
    currencies = ["euro", "yuan", "lira", "rublo", "dolar"]

    html = fetch_html(url)
    soup = parse_html(html)

    data = []
    scraped_at = datetime.now()
    logging.info(f"Scraping performed at: {scraped_at}")
    if soup:
        for currency in currencies:
            exchange_rate = extract_strong_text_by_id(soup, currency)
            logging.info(f"{currency.capitalize()} exchange rate: {exchange_rate if exchange_rate else 'Not found'}")
            data.append((currency, exchange_rate))

    # PostgreSQL connection parameters from environment variables
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 5432))

    conn = connect_postgres(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
    if conn:
        create_table_if_not_exists(conn)
        insert_currency_data(conn, data, scraped_at)
        conn.close()
        logging.info("Currency data inserted into PostgreSQL.")
    
