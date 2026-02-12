"""Module invoking Cloud Functions for code logic and Firebase integration"""
import base64
import logging
import functions_framework
from cloudevents.http.event import CloudEvent
from .strategy import main_strategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Triggered from a message on a Cloud Pub/Sub topic
#Scheduled function to run every weekday at 9:30 am
"""@functions_framework.cloud_event
def subscribe(cloud_event: CloudEvent) -> (None):

    print("Cloud function running!")
    print(
        "Pub/Sub message: " + base64.b64decode(cloud_event.data["message"]["data"]).decode()
            )
    if base64.b64decode(cloud_event.data["message"]["data"]).decode() == "buy":
        print("Executing buy strat now!")
        buy_instance = main_strategy.ClientInstance()
        buy_instance.execute_buy_strategy()
        logger.info("Buy Strategy complete!")
        return None

    if base64.b64decode(cloud_event.data["message"]["data"]).decode() == "sell":
        print("Executing sell strat now!")
        sell_instance = main_strategy.ClientInstance()
        sell_instance.execute_sell_strategy()
        logger.info("Sell strategy complete!")
        return None

    if base64.b64decode(cloud_event.data["message"]["data"]).decode() == "push":
        print("Pushing data now!")
        sell_instance = main_strategy.ClientInstance()
        sell_instance.push_port_orders()
        logger.info("Ports were pushed successfully!")
        return None

    #Testing the connection
    print(
        "TEST Pub/Sub message:" + base64.b64decode(cloud_event.data["message"]["data"]).decode()
        )
    return None"""

# Triggered from a message on a Cloud Pub/Sub topic
#Scheduled function to run every weekday at 9:30 am
@functions_framework.cloud_event
def subscribe(cloud_event: CloudEvent) -> (None):
    """
    Recieves a scheduled cloud pub/sub event and is executed. Args: CloudEvent
    """
    logger.info("Cloud function running!")

    msg = base64.b64decode(cloud_event.data["message"]["data"]).decode()
    logger.info("Pub/Sub message: %s", msg)

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