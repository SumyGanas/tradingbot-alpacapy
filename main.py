"""Module invoking Cloud Functions for code logic and Firebase integration"""
import base64
import logging
import functions_framework
from cloudevents.http.event import CloudEvent
from .strategy import main_strategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@functions_framework.cloud_event
def subscribe(cloud_event: CloudEvent) -> (None):
    """
    Triggered from a message on a Cloud Pub/Sub topic
    Scheduled function to run every weekday at 9:30 am
    Recieves a scheduled cloud pub/sub event and is executed. Args: CloudEvent
    """
    msg = base64.b64decode(cloud_event.data["message"]["data"]).decode()

    trading = main_strategy.ClientInstance()

    if msg == "buy":
        logger.info("Executing buy strat now!")
        trading.execute_buy_strategy()

    elif msg == "sell":
        logger.info("Executing sell strat now!")
        trading.execute_sell_strategy()

    elif msg == "push":
        logger.info("Pushing data now!")
        trading.push_port_orders()