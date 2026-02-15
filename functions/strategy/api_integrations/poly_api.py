"""Module returns RSI and EMA data from Polygon.io API"""
import logging
import os
from dotenv import load_dotenv
from massive import RESTClient
from requests import HTTPError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()
client = RESTClient(api_key=os.getenv("MASSIVE_API_KEY"))


def get_indicator(tckr, indicator) -> (int|tuple[int,int,int]):
    """collects RSI or MACD data provided a ticker and returns it"""
    indicator = indicator.lower()
    if indicator == "rsi":
        try:
            rsi = client.get_rsi(
                ticker = str(tckr),
                timespan="hour",
                window=3,
                series_type="close",
                limit=1,
            )
            if rsi:
                return rsi.values[0].value # pyright: ignore

        except HTTPError as exc:
            raise RuntimeError("Error fetching RSI data from polygon API: ") from exc

    if indicator == "macd":
        try:
            macd = client.get_macd(
                ticker= str(tckr),
                timespan="hour",
                short_window=12,
                long_window=26,
                signal_window=9,
                series_type="close",
                limit=1,
            )

            signal = macd.values[0].signal # pyright: ignore
            histogram = macd.values[0].histogram # pyright: ignore
            return macd.values[0].value, signal, histogram # pyright: ignore

        except Exception as exc:
            raise RuntimeError("Error fetching MACD data from polygon API") from exc


    raise ValueError("Unknown Value Error occured during calling Poly API")
