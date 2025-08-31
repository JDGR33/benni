import requests
from bs4 import BeautifulSoup
import logging
# TODO: Take a look at how to solve the ssl problem
# TODO: Data base connecction
# TODO: 

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
        response = requests.get(url, verify=False)#, verify=certifi.where())
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
    url = "https://www.bcv.org.ve/"  
    currencies = ["euro","yuan","lira","rublo","dolar"]

    html = fetch_html(url)
    soup = parse_html(html)
    if soup:
        for currency in currencies:
            exchange_rate = extract_strong_text_by_id(soup, currency)
            logging.info(f"{currency.capitalize()} exchange rate: {exchange_rate if exchange_rate else 'Not found'}")