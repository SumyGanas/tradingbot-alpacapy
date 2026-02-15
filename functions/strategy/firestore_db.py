"""Firestore DB module"""
from datetime import date
import logging
import uuid
import firebase_admin
from firebase_admin import firestore
from google.api_core.exceptions import PermissionDenied, ServiceUnavailable, DeadlineExceeded, InvalidArgument

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Application Default credentials are automatically created.
app = firebase_admin.initialize_app()
db = firestore.client()

def push_portfolio(trade_object): #tradeaccount object
    """
    Pushes portfolio data (TradingAccount objects) to the portfolio 
    firebase collection
    """
    data = vars(trade_object)
    for k,v in data.items():
        if isinstance(v, uuid.UUID):
            data[k] = str(v)
    try:
        db.collection('portfolio').document(str(date.today())).set(data)
    except (PermissionDenied, ServiceUnavailable, DeadlineExceeded, InvalidArgument) as exc:
        logger.error("Failed to push portfolio data to the firebase collection: %s", exc)

def push_order(order_list):
    """
    Pushes buy order and sell order data (Order objects from alpaca backend) 
    to the orders firebase collection
    """
    doc_ref = db.collection('orders').document(str(date.today()))
    # Create a sub-collection
    subcollection_ref = doc_ref.collection('orders')

    # Add documents to the sub-collection if needed
    if order_list is not None and len(order_list) > 0:
        try:
            for order in order_list:
                data = vars(order)
                for k,v in data.items():
                    if isinstance(v, uuid.UUID):
                        data[k] = str(v)
                subcollection_ref.add(data)
        except (PermissionDenied, ServiceUnavailable, DeadlineExceeded, InvalidArgument) as exc:
            logger.error("Failed to push order data to the firebase collection: %s", exc)
    else:
        logger.info("No new order data today!")


def push_buy_executions(order_list):
    """
    Pushes buy order execution data to the database
    """
    doc_ref = db.collection('buy_executions').document(str(date.today()))

    subcollection_ref = doc_ref.collection('buy_orders')

    if order_list is not None and len(order_list) > 0:
        try:
            for order in order_list:
                data = vars(order)
                for k,v in data.items():
                    if isinstance(v, uuid.UUID):
                        data[k] = str(v)
                subcollection_ref.add(data)
        except (PermissionDenied, ServiceUnavailable, DeadlineExceeded, InvalidArgument) as exc:
            logger.error("Failed to push buy order execution data to the firebase collection: %s", exc)
    else:
        logger.info("No new order data today!")

def push_sell_executions(order_list):
    """
    Pushes sell order execution data to the database
    """
    doc_ref = db.collection('sell_executions').document(str(date.today()))

    subcollection_ref = doc_ref.collection('sell_orders')

    if order_list is not None and len(order_list) > 0:
        try:
            for order in order_list:
                data = vars(order)
                for k,v in data.items():
                    if isinstance(v, uuid.UUID):
                        data[k] = str(v)
                subcollection_ref.add(data)
        except (PermissionDenied, ServiceUnavailable, DeadlineExceeded, InvalidArgument) as exc:
            logger.error("Failed to push sell order execution data to the firebase collection: %s", exc)
    else:
        logger.info("No new order data today!")


# DD78F
