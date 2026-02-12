"""Contains code to facilitate execution of the algo-trading strategy"""
import os
import logging
from datetime import datetime
import requests
from ratelimit import limits, sleep_and_retry
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.models import Order, Position
from alpaca.trading.enums import OrderSide, TimeInForce
from .api_integrations import poly_api, fmp_api
from . import firestore_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_env() -> (dict):
    """access environment variables for API Secrets"""
    env_variable_names = ['ALPACA_KEY', 'ALPACA_SECRET', 'POLY_KEY', 'FMP_KEY']
    env_variables = {}
    for name in env_variable_names:
        env_variables[name] = str(os.environ.get(name))
    return env_variables

class StrategyHandler():
    """
    Contains methods for order creation and execution, plus strategy logic
    """
    def __init__(self, client: TradingClient, secret: dict):
        self.trading_client = client
        self.secret = secret

    def check_fund(self, account_details) -> (bool):
        """checks portfolio value and returns true if (Cash > 25000 for PDT"""
        portfolio_value = account_details.cash
        return float(portfolio_value) >= 25000

    def check_spend(self, allocation_limit, account_details, spent_already) -> (bool):
        """
        Returns true if you have available daily stock allocation
        """
        portfolio_value = account_details.cash
        max_spend = float(portfolio_value) * allocation_limit
        return spent_already < max_spend

    def check_if_buy(self, allocation_limit, spent_already, account_details):
        """ 
        Returns true if you can buy stocks for the day
        """
        check_fund = self.check_fund(account_details)
        check_spend = self.check_spend(allocation_limit,account_details,spent_already)

        return check_fund and check_spend

    @sleep_and_retry
    @limits(calls=5, period=61)
    def get_ta_data(self, ticker: str, indicator: str) -> (float)|(tuple[float, float, float]):
        """Returns RSI or MACD value(s) from Polygon API"""
        if indicator == "rsi":
            rsi = poly_api.get_indicator(ticker, "rsi")
            return float(rsi)
        if indicator == "macd":
            value, signal, hist = poly_api.get_indicator(ticker, "macd")
            return float(value), float(signal), float(hist)
        return None

    #@limits(calls=200, period=61)
    def get_quote(self, ticker:str):
        """
        Gets latest stock quote from alpacapy
        """
        ticker = ticker.upper()
        url = f"https://data.alpaca.markets/v2/stocks/quotes/latest?symbols={ticker}&feed=iex"
        headers = {"accept": "application/json",
                   "APCA-API-KEY-ID": self.secret['ALPACA_KEY'],
                   "APCA-API-SECRET-KEY":self.secret['ALPACA_SECRET']
                   }
        try:
            response = requests.get(url, headers=headers, timeout=4)
            if response.status_code == 200:
                result = response.json()
        except requests.HTTPError:
            logger.error(
                "HTTP error encountered while fetching Alpaca stock quote: %s", 
                response.raise_for_status()
                )
        return result

    @sleep_and_retry
    @limits(calls=200, period=61)
    def buy_signal(self, ticker: str, allocation: float,
                    spent_already: float) -> (tuple[str,float]):
        """
        Returns buy, sell, do nothing, and no funds remaining signals for a watchlist 
        ticker and the amount of cash remaining for the day
        """
        #getting new account details every call to account for changes
        account_details = self.trading_client.get_account()
        cash_available = float(account_details.cash)
        if self.check_if_buy(allocation, spent_already, account_details):
            value, signal, hist = self.get_ta_data(ticker, "macd")
            if value > signal and hist > 0.0:
                rsi = self.get_ta_data(ticker, "rsi")
                if rsi < 35.00:
                    return ("buy", cash_available)
            return ("do nothing", cash_available)
        return ("no funds", cash_available) #no funds remaining

    def quantity_calc(self, signal:str, ticker:str, portval: float) -> (int):
        """
        Returns stock quantity to buy or sell
        """
        if signal == "buy":
            quote = self.get_quote(ticker)
            ticker = ticker.upper()
            unitprice = quote["quotes"][ticker]["ap"]
            if float(unitprice) < 500.00 and float(unitprice) > 0:
                buying_price = portval*0.05
                quantity = buying_price/unitprice
                truncated_qty = int(quantity) #preventing fractional orders
                return truncated_qty
            if 500.00 < float(unitprice) and float(unitprice) < 10000.00:
                return 1.00 #fail-safe making sure to buy at least 1
        elif signal == "sell":
            position = self.trading_client.get_open_position(ticker)
            if position is not None:
                quantity = position.qty_available
                return quantity
            print("Position not available")
        return None

    def create_order_data(self, symb, qt, order_type) -> (MarketOrderRequest):
        """
        Creates final format of the market order

        Args: Symbol: int, Qty: float, Order_type: str 

        Returns / Raises: MarketOrderRequest / Validation error if bad order data
        """
        symb = symb.upper()
        if order_type == "buy":
            ordrtype = OrderSide.BUY
        if order_type == "sell":
            ordrtype = OrderSide.SELL
        market_order_data = MarketOrderRequest(
                    symbol=str(symb),
                    qty=float(qt),
                    side=ordrtype,
                    #Canceled if unfilled after the closing auction
                    time_in_force=TimeInForce.DAY #(day, gtc, opg, cls, ioc, fok)
                    )

        return market_order_data

    def execute_order(self, market_order_data: MarketOrderRequest) -> (Order):
        """
        Executes a market order 

        Returns: Order
        """
        try:
            market_order = self.trading_client.submit_order(order_data = market_order_data)
            logger.info("Market order placed!")
            return market_order
        except requests.HTTPError:
            logger.error("Error occured while submitting market order: %s", requests.HTTPError)
            raise

    def sell_signal(self, position: Position) -> (str|None):
        """
        Checks a position and returns a sell signal if the TA or the ROI matches
        """
        value, signal, hist = self.get_ta_data(position.symbol, "macd")
        if value < signal and hist < 0.0:
            rsi = self.get_ta_data(position.symbol, "rsi")
            if rsi > 65.00:
                return "sell"

        p_and_l = float(position.unrealized_plpc)
        if p_and_l >= 0.05:
            return "sell"

        return None

class WatchlistHandler():
    """
    Contains methods that decide which stocks the strategy is focusing on for the day and 
    methods to check existing wachlist positions
    """
    def __init__(self, secret, max_stock_price=5000.0, max_watchlist_len=30):
        self.secret = secret
        self.max_stock_price = max_stock_price
        self.max_watchlist_len = max_watchlist_len

    def create_watchlist(self) -> (list):
        """returns the watchlist of 30 stocks to focus on"""
        stock_list = fmp_api.get_jsonparsed_data("active", self.secret['FMP_KEY'])

        return stock_list

    def approve_watchlist(self, stock_list: list[dict]) -> (list):
        """Approves watchlist"""
        watchlist = []
        for stock in stock_list:
            if stock["price"] <= self.max_stock_price:
                watchlist.append(stock)

        if len(watchlist) > self.max_watchlist_len:
            watchlist = watchlist[:self.max_watchlist_len]

        return watchlist

class StrategyExecution():
    """
    Contains methods to automate trading strategy execution,
    controls the order/trade websocket connection and holds the program state. 
    Args - what % of port to allot per day
    """
    def __init__(self, allocation_limit: float, client: TradingClient, secret: dict):
        self.allocation_limit = allocation_limit
        self.trading_client = client
        self.strategy_handler = StrategyHandler(client, secret)
        self.watchlist_handler = WatchlistHandler(secret)

    def buy_strategy(self) -> (list|None):
        """
        Begins running automated strategy by creating a watchlist 
        and buying positions based on a signal and 
        returns total amount spent and orders placed that day
        """
        logger.info("Buy strat has begun!")
        spent_already = 0.0
        #create a new watchlist -> watchlist
        stocklist = self.watchlist_handler.create_watchlist()
        watchlist = self.watchlist_handler.approve_watchlist(stocklist)
        # run operations on new watchlist
        orderlist = []
        for stock in watchlist:
            ticker = stock["symbol"]
            signal, port_val = self.strategy_handler.buy_signal(
                ticker, self.allocation_limit, spent_already
                )
            if signal == "buy":
                qty = self.strategy_handler.quantity_calc(signal, ticker, port_val)
                if qty is not None:
                    logger.info("Buying %s stocks of %s", qty, ticker)
                    order_data = self.strategy_handler.create_order_data(
                        stock["symbol"], qty, "buy"
                        )
                    order = self.strategy_handler.execute_order(order_data)
                    orderlist.append(order)
                    if order.filled_avg_price is not None:
                        spent_already += float(order.filled_avg_price)
                    else:
                        quote = self.strategy_handler.get_quote(ticker)
                        unitprice = quote["quotes"][ticker]["ap"]
                        spent_already += float(unitprice)*qty
            if signal == "no funds":
                logger.info("Finished buying for the day")
                break
        if spent_already > 0:
            logger.info("Amount spent: %s", spent_already)
            return orderlist
        if spent_already == 0:
            logger.info("No stocks to buy today!")
            return None
        raise RuntimeError("Unknown Error calculating total amount spent on daily purchases")

    def sell_strategy(self) -> (list|None):
        """
        Executes the sell and roi strategy functions
        """
        logger.info("Sell strat has begun!")
        try:
            positions = self.trading_client.get_all_positions()
        except requests.HTTPError:
            logger.error("Error getting position from alpaca client: %s", requests.HTTPError)
            raise

        sell_orders = []
        if len(positions) > 0:
            for position in positions:
                sell_signal = self.strategy_handler.sell_signal(position)
                if sell_signal == "sell": #sell all of the current position
                    order_data = self.strategy_handler.create_order_data(
                        position.symbol, position.qty_available, "sell"
                        )
                    order = self.strategy_handler.execute_order(order_data)
                    sell_orders.append(order)
                    logger.info("Sell order placed: %s", order)

        return sell_orders

    def create_data(self)-> (tuple[str, dict]):
        """ 
        Creates and returns EOD DB data
        """
        try:
            trading_account = self.trading_client.get_account()
        except requests.HTTPError:
            logger.error(
                "HTTP Error getting account from Alpaca to create data: %s", requests.HTTPError
                )
            raise

        current_date = datetime.now().date()
        yesterday_datetime = datetime.combine(current_date, datetime.min.time())

        order_request = GetOrdersRequest(
            status="closed",
            limit=500,
            after=yesterday_datetime
        )

        try:
            orders = self.trading_client.get_orders(order_request)
        except requests.HTTPError:
            logger.error(
                "HTTP Error getting orders from Alpaca to create data: %s", requests.HTTPError
                )
            raise

        return trading_account, orders

    def push_data(self, side: str, orders: list[Order]):
        """
        Pushes data to the DB
        """
        if orders is not None and len(orders) > 0:
            if side == "buy":
                firestore_db.push_buy_executions(orders)
            if side =="sell":
                firestore_db.push_sell_executions(orders)

class ClientInstance:
    """Used to initialize a client instance for every instance of a strategy operation"""
    def __init__(self):
        self.env_vars = get_env()
        self.client = TradingClient(
            self.env_vars['ALPACA_KEY'], self.env_vars['ALPACA_SECRET'], paper=True
            )
        self.strategyexec = StrategyExecution(0.02, self.client, self.env_vars)

    def execute_buy_strategy(self):
        """initialize a buy instance and push results"""
        buy_orders = self.strategyexec.buy_strategy()
        self.strategyexec.push_data("buy", buy_orders)

    def execute_sell_strategy(self):
        """initialize a sell instanceand push results"""
        sell_orders = self.strategyexec.sell_strategy()
        self.strategyexec.push_data("sell", sell_orders)

    def push_port_orders(self):
        """fetch and push portfolio and pure-order data"""
        account_info, order_list = self.strategyexec.create_data()
        firestore_db.push_portfolio(account_info)
        firestore_db.push_order(order_list)

def test_db_con():
    """
    Test function for checking database connection
    """
    env_vars = get_env()
    trading_client = TradingClient(env_vars['ALPACA_KEY'], env_vars['ALPACA_SECRET'], paper=True)
    strategyexec = StrategyExecution(0.02, trading_client, env_vars)
    ta, orders = strategyexec.create_data()
    firestore_db.push_portfolio(ta)
    firestore_db.push_order(orders)
