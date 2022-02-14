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

    @classmethod
    def get_or_create(cls, **kwargs):
        r = cls.get(**kwargs)
        if r is None:
            return cls(**kwargs), True
        else:
            return r, False

    @classmethod
    def update_or_create(cls, **kwargs):
        try:
            instance = cls[tuple(kwargs[pk_attr.name] for pk_attr in cls._pk_attrs_)]
        except Exception as err:
            return cls(**kwargs)
        else:
            instance.set(**kwargs)
            return instance


# class Agreement(db.Entity):
#     id = PrimaryKey(int, auto=True)
#     count = Optional(int, default=0)
#     price_sum = Optional(float, default=0.0)
#     product = Set(ProductAnalytics, reverse='agreement', nullable=False)
#
#
# class Equipment(db.Entity):
#     id = PrimaryKey(int, auto=True)
#     count = Optional(int, default=0)
#     price_sum = Optional(float, default=0)
#     product = Set(ProductAnalytics, reverse='equipment', nullable=False)
#
#
# class Delivery(db.Entity):
#     id = PrimaryKey(int, auto=True)
#     count = Optional(int, default=0)
#     price_sum = Optional(float, default=0)
#     product = Set(ProductAnalytics, reverse='delivery', nullable=False)
#
#
# class Completed(db.Entity):
#     id = PrimaryKey(int, auto=True)
#     count = Optional(int, default=0)
#     price_sum = Optional(float, default=0)
#     product = Set(ProductAnalytics, reverse='completed', nullable=False)
#
#
# class Canceled(db.Entity):
#     id = PrimaryKey(int, auto=True)
#     count = Optional(int, default=0)
#     price_sum = Optional(float, default=0)
#     product = Set(ProductAnalytics, reverse='canceled', nullable=False)


db.generate_mapping(create_tables=True)
