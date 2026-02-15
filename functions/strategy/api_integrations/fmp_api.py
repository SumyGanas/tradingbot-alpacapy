"""Module returns stock market data from the FMP (Financial Modeling Prep) API"""
import json
import logging
from urllib.request import urlopen
from requests import HTTPError
import certifi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_jsonparsed_data(datatype, key) -> (list|None):
    """returns data from API endpoint (arg: api url)"""
    try:
        if datatype == "gainer":
            url = f'https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={key}'
            response = urlopen(url, cafile=certifi.where())
            data = response.read().decode("utf-8")
            return json.loads(data)
        if datatype == "active":
            url = f'https://financialmodelingprep.com/api/v3/stock_market/actives?apikey={key}'
            response = urlopen(url, cafile=certifi.where())
            data = response.read().decode("utf-8")
            return json.loads(data)
    except HTTPError as exc:
        logger.error("Error occured while getting data from FMP API: %s", exc)
        raise RuntimeError("Error occured while getting data from FMP API") from exc
    return None
#URL endpoints used
#mkt_gainer_url = f'https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={key}'
#mkt_active_url = f'https://financialmodelingprep.com/api/v3/stock_market/actives?apikey={key}'
