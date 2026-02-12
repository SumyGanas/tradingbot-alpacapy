"""Module returns RSI and EMA data from Polygon.io API"""
import logging
import os
from polygon import RESTClient
# from polygon.rest.models.indicators import SingleIndicatorResults, MACDIndicatorResults
from requests import HTTPError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
c = RESTClient(api_key=os.environ.get("POLY_KEY"))


def get_indicator(tckr, indicator):
    """collects RSI or MACD data provided a ticker and returns it"""
    #5 API calls per minute
    #wait_time = 61
    indicator = indicator.lower()
    if indicator == "rsi":
        #Trying 3 times
        #for _ in range(3):
        try:
            result = c.get_rsi(
                ticker = str(tckr),
                timespan="hour",
                window=3,
                series_type="close",
                limit=1,
            )
            rsi_value = result.values[0].value
            return rsi_value

        except HTTPError as exc:
            logger.error("Error fetching RSI data from polygon API: %s", exc)
            raise RuntimeError("Error fetching RSI data from polygon API: ") from exc

    if indicator == "macd":
        try:
            result = c.get_macd(
                ticker= str(tckr),
                timespan="hour",
                short_window=12,
                long_window=26,
                signal_window=9,
                series_type="close",
                limit=1,
            )
            macd = result.values[0].value
            signal = result.values[0].signal
            histogram = result.values[0].histogram
            return macd, signal, histogram

        except Exception as exc:
            logger.error("Error fetching MACD data from polygon API: %s", exc)
            raise RuntimeError("Error fetching MACD data from polygon API") from exc


    logger.error("Unknown Value Error occured during calling Poly API")
    return ValueError("Unknown Value Error occured during calling Poly API")
