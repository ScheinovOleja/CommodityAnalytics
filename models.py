import configparser
import datetime
import os

from pony.orm import Database, PrimaryKey, Optional, Required

config = configparser.ConfigParser()
config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.cfg'))

db = Database()
db.bind(**config['DATABASE'], provider='postgres')


class ProductAnalytics(db.Entity):
    _table_ = 'product_analytics'
    id = PrimaryKey(int, auto=True)
    product_id = Required(int, nullable=False, default=0)
    category = Required(str, nullable=False)
    name = Required(str, nullable=False)
    proportions = Optional(str, nullable=True)
    article = Optional(str, nullable=False)
    ordered_count = Optional(int)
    price_sum = Optional(float)
    design_method = Optional(str)
    new_price_sum = Optional(float, default=0.0, nullable=True)
    new_count = Optional(int, default=0, nullable=True)
    approval_price_sum = Optional(float, default=0.0, nullable=True)
    approval_count = Optional(int, default=0, nullable=True)
    equipment_price_sum = Optional(float, default=0.0, nullable=True)
    equipment_count = Optional(int, default=0, nullable=True)
    delivery_price_sum = Optional(float, default=0.0, nullable=True)
    delivery_count = Optional(int, default=0, nullable=True)
    point_issue_orders_price_sum = Optional(float, default=0.0, nullable=True)
    point_issue_orders_count = Optional(int, default=0, nullable=True)
    canceled_price_sum = Optional(float, default=0.0, nullable=True)
    canceled_count = Optional(int, default=0, nullable=True)
    completed_price_sum = Optional(float, default=0.0, nullable=True)
    completed_count = Optional(int, default=0, nullable=True)
    create_date_at = Optional(datetime.datetime)
    create_date_to = Optional(datetime.datetime)


db.generate_mapping(create_tables=True)
