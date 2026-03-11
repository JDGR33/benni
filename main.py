# Add psycopg2 for PostgreSQL integration
import requests
from bs4 import BeautifulSoup
import logging
import certifi
import urllib3

# PostgreSQL and dotenv integration
import psycopg2
from dotenv import load_dotenv
import os
from datetime import datetime
import time


# TODO: Take a look at how to solve the ssl problem
# TODO: Data base connection
def connect_postgres(
    dbname, user, password, host="localhost", port=5432, retries=5, delay_seconds=5
):
    """Connect to PostgreSQL and return connection."""
    for attempt in range(1, retries + 1):
        try:
            conn = psycopg2.connect(
                dbname=dbname, user=user, password=password, host=host, port=port
            )
            logging.info("Connected to PostgreSQL database.")
            return conn
        except Exception as e:
            logging.error(
                f"PostgreSQL connection error (attempt {attempt}/{retries}): {e}"
            )
            if attempt < retries:
                time.sleep(delay_seconds)
    return None


def create_table_if_not_exists(conn):
    """Create currency_rates table if it doesn't exist."""
    query = """
    CREATE TABLE IF NOT EXISTS currency_rates (
        id SERIAL PRIMARY KEY,
        currency VARCHAR(20) NOT NULL,
        rate VARCHAR(50),
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()


def insert_currency_data(conn, data, scraped_at):
    """Insert currency data into the table."""
    with conn.cursor() as cur:
        for currency, rate in data:
            cur.execute(
                "INSERT INTO currency_rates (currency, rate, scraped_at) VALUES (%s, %s, %s)",
                (currency, rate, scraped_at),
            )
        conn.commit()


# Configure logging
logging.basicConfig(level=logging.INFO)


def extract_strong_text_by_id(soup, div_id):
    """Return text inside <strong> tag within a div of given id."""
    div = soup.find("div", id=div_id)
    if div:
        strong_tag = div.find("strong")
        if strong_tag:
            return strong_tag.get_text(strip=True)
    return None


def fetch_html(url, retries=3, delay_seconds=5, allow_insecure_ssl_fallback=False):
    """Fetch HTML content from a URL."""
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, verify=certifi.where(), timeout=20)
            response.raise_for_status()
            logging.info(f"Fetched content from {url}")
            return response.text
        except requests.exceptions.SSLError as e:
            logging.error(
                f"SSL error fetching {url} (attempt {attempt}/{retries}): {e}"
            )
            if allow_insecure_ssl_fallback:
                logging.warning("Falling back to insecure SSL request (verify=False).")
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                try:
                    response = requests.get(url, verify=False, timeout=20)
                    response.raise_for_status()
                    logging.info(
                        f"Fetched content from {url} with insecure SSL fallback"
                    )
                    return response.text
                except requests.RequestException as fallback_error:
                    logging.error(
                        f"Insecure SSL fallback failed for {url} (attempt {attempt}/{retries}): {fallback_error}"
                    )
            if attempt < retries:
                time.sleep(delay_seconds)
        except requests.RequestException as e:
            logging.error(f"Error fetching {url} (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(delay_seconds)
    return None


def parse_html(html):
    """Parse HTML content and return BeautifulSoup object."""
    if html:
        soup = BeautifulSoup(html, "html.parser")
        return soup
    else:
        logging.error("No HTML to parse.")
        return None


if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    url = "https://www.bcv.org.ve/"
    currencies = ["euro", "yuan", "lira", "rublo", "dolar"]

    # PostgreSQL connection parameters from environment variables
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 5432))

    FETCH_RETRIES = int(os.getenv("FETCH_RETRIES", 3))
    FETCH_RETRY_DELAY = int(os.getenv("FETCH_RETRY_DELAY", 5))
    DB_RETRIES = int(os.getenv("DB_RETRIES", 5))
    DB_RETRY_DELAY = int(os.getenv("DB_RETRY_DELAY", 5))
    ALLOW_INSECURE_SSL_FALLBACK = (
        os.getenv("ALLOW_INSECURE_SSL_FALLBACK", "true").lower() == "true"
    )

    html = fetch_html(
        url,
        retries=FETCH_RETRIES,
        delay_seconds=FETCH_RETRY_DELAY,
        allow_insecure_ssl_fallback=ALLOW_INSECURE_SSL_FALLBACK,
    )
    soup = parse_html(html)

    data = []
    scraped_at = datetime.now()
    logging.info(f"Scraping performed at: {scraped_at}")
    if soup:
        for currency in currencies:
            exchange_rate = extract_strong_text_by_id(soup, currency)
            logging.info(
                f"{currency.capitalize()} exchange rate: {exchange_rate if exchange_rate else 'Not found'}"
            )
            data.append((currency, exchange_rate))

    conn = connect_postgres(
        DB_NAME,
        DB_USER,
        DB_PASSWORD,
        DB_HOST,
        DB_PORT,
        retries=DB_RETRIES,
        delay_seconds=DB_RETRY_DELAY,
    )
    if conn:
        create_table_if_not_exists(conn)
        if data:
            insert_currency_data(conn, data, scraped_at)
            logging.info("Currency data inserted into PostgreSQL.")
        else:
            logging.warning("No currency data extracted; nothing inserted.")
        conn.close()
