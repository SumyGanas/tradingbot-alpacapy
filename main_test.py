from datetime import datetime
import json
from strategy import main_strategy


class FakeOrder():
    def __init__(self, created_at, ordertype):
        self.created_at = created_at
        self.type = ordertype

fake_order = FakeOrder(datetime.now(), "buy")


fake_order_two = FakeOrder(datetime.now(), "buy"
)

fake_order_three = FakeOrder(datetime.now(), "sell")

fake_order_four = FakeOrder(datetime.now(), "sell")

fake_order_dict = vars(fake_order)
fake_order_dict_two = vars(fake_order_two)
fake_order_dict_three = vars(fake_order_three)
fake_order_dict_four = vars(fake_order_four)


fake_order_json = json.dumps(fake_order_dict, default=str)
fake_order_two_json = json.dumps(fake_order_dict_two, default=str)
fake_order_three_json = json.dumps(fake_order_dict_three, default=str)
fake_order_four_json = json.dumps(fake_order_dict_four, default=str)

buy_orders = [fake_order_json, fake_order_two_json]
sell_orders = [fake_order_three_json, fake_order_four_json]

#main_strategy.test_db_con()
