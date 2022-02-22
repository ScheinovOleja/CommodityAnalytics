import configparser
import os
import re
from datetime import datetime
import retailcrm
from pony.orm import db_session

from models import ProductAnalytics
import argparse


class ParserRetailCRM:

    def __init__(self, date_at, date_to):
        """
        Инициализация всего необходимого

        :param date_at:
        :param date_to:
        """
        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.cfg'))
        self.client = retailcrm.v5(self.config.get('API', 'URL'), self.config.get('API', 'KEY'))
        self.date_at = datetime.strptime(date_at, "%Y-%m-%d")
        self.date_to = datetime.strptime(date_to, "%Y-%m-%d")
        self.new_iter = True
        self.new_price_sum = 0
        self.new_count = 0
        self.approval_price_sum = 0
        self.approval_count = 0
        self.equipment_price_sum = 0
        self.equipment_count = 0
        self.delivery_price_sum = 0
        self.delivery_count = 0
        self.point_issue_orders_price_sum = 0
        self.point_issue_orders_count = 0
        self.canceled_price_sum = 0
        self.canceled_count = 0
        self.completed_price_sum = 0
        self.completed_count = 0

    def init_count_and_price_sum(self):
        """
        Обнуление суммы и количества товаров в каждой категории(локальное)

        :return:
        """
        self.new_price_sum = 0
        self.new_count = 0
        self.approval_price_sum = 0
        self.approval_count = 0
        self.equipment_price_sum = 0
        self.equipment_count = 0
        self.delivery_price_sum = 0
        self.delivery_count = 0
        self.point_issue_orders_price_sum = 0
        self.point_issue_orders_count = 0
        self.canceled_price_sum = 0
        self.canceled_count = 0
        self.completed_price_sum = 0
        self.completed_count = 0

    @staticmethod
    def auxiliary_calc(price_sum, count, order, product):
        """
        Расчет суммы и количества товаров(сюда перенаправление из "calc_count_and_price_sum"
        :param price_sum: текущая сумма товаров в категории
        :param count: текущее количество товаров в категории
        :param order: заказ
        :param product: товар
        :return:
        """
        for item in order['items']:
            for offer in product['offers']:
                if item['offer']['displayName'] == offer['name']:
                    try:
                        for price in item['prices']:
                            price_sum += price.get('price') * price.get('quantity')
                            count += item.get('quantity')
                    except Exception as err:
                        print(err)
        return price_sum, count

    def calc_count_and_price_sum(self, status, order, product, history_status):
        """
        перенаправление на расчет количества и суммы в каждой категории статусов

        :param status: статус
        :param order: заказ
        :param product: товар
        :param history_status: статус для "ПВЗ" и "Заказы от 20"
        :return:
        """
        try:
            if status['code'] == 'new' or history_status['newValue']['code'] == 'orders20':
                self.new_price_sum, self.new_count = self.auxiliary_calc(self.new_price_sum, self.new_count, order,
                                                                         product)
            elif status['code'] == 'approval':
                self.approval_price_sum, self.approval_count = self.auxiliary_calc(self.approval_price_sum,
                                                                                   self.approval_count, order, product)
            elif status['code'] == 'assembling':
                self.equipment_price_sum, self.equipment_count = self.auxiliary_calc(self.equipment_price_sum,
                                                                                     self.equipment_count, order,
                                                                                     product)
            elif status['code'] == 'delivery':
                self.delivery_price_sum, self.delivery_count = self.auxiliary_calc(self.delivery_price_sum,
                                                                                   self.delivery_count, order, product)
            elif status['code'] == 'complete':
                self.completed_price_sum, self.completed_count = self.auxiliary_calc(self.completed_price_sum,
                                                                                     self.completed_count, order,
                                                                                     product)
            elif status['code'] == 'cancel':
                self.canceled_price_sum, self.canceled_count = self.auxiliary_calc(self.canceled_price_sum,
                                                                                   self.canceled_count, order, product)
        except TypeError:
            # TODO если не найдено status['code'](только в случае с "готов к ПВЗ") перенаправление для расчета в ПВЗ
            if 'gotov-k-pvz' == status:
                self.point_issue_orders_price_sum, self.point_issue_orders_count = self.auxiliary_calc(
                    self.point_issue_orders_price_sum,
                    self.point_issue_orders_count, order, product)

    @staticmethod
    def calc_proportion_count_price(order, product):
        """
        Расчет размера, количества и суммы продукта

        :param order: заказ
        :param product: товар
        :return:
        """
        # TODO перебор по всем товарам в заказе
        for item in order['items']:
            for offer in product['offers']:
                if item['offer']['displayName'] == offer['name']:
                    try:
                        proportions_product = re.findall('\(\S*\)', item.get('offer').get('displayName'))[0]
                    except IndexError:
                        proportions_product = '-'
                    ordered_count = offer.get('quantity')
                    price_sum = 0
                    for price in item['prices']:
                        price_sum = price.get('price') * price.get('quantity')
                    return proportions_product, ordered_count, price_sum
        else:
            return None, None, None

    def calc_all_history(self, history_status, all_status, product, order):
        """
        Перебор всех статусов заказа и дальнейший расчет.

        :param history_status: список изменений статусов заказа
        :param all_status: все статусы(новый, согласование и тд)
        :param product: товар
        :param order: заказ
        :return:
        """
        for status in all_status.values():
            if history_status['newValue']['code'] in status['statuses']:
                # TODO получение группы
                group_product = self.client.product_groups(
                    filters={'ids': [product["groups"][0]['id']]},
                    limit=100).get_response()['productGroup'][0]
                proportions_product, ordered_count, price_sum = self.calc_proportion_count_price(order, product)
                if not price_sum:
                    continue
                try:
                    order_method = self.client.order_methods().get_response()['orderMethods'].get(
                        order['orderMethod'])['name']
                except KeyError:
                    order_method = '-'
                if history_status['newValue']['code'] == 'gotov-k-pvz':
                    status = history_status['newValue']['code']
                self.calc_count_and_price_sum(status, order, product, history_status)
                self.create_product(product, group_product, proportions_product, ordered_count, price_sum, order_method)
                self.new_iter = False

    @db_session
    def create_product(self, product, group_product, proportions_product, ordered_count, price_sum, order_method):
        """
        Создание записи в бд

        :param product: товар
        :param group_product: группа товара
        :param proportions_product: размеры товара
        :param ordered_count: остатки на складе
        :param price_sum: стоимость продажи
        :param order_method: метод формирования заказа
        :return:
        """
        # TODO получение записи из БД
        analytics = ProductAnalytics.get(
            product_id=product['id'],
            category=group_product['name'],
            name=product['name'],
            proportions=proportions_product,
            article=product['article'],
            ordered_count=ordered_count,
            price_sum=price_sum,
            design_method=order_method,
            create_date_at=self.date_at,
            create_date_to=self.date_to,
        )
        # TODO Если запись в бд имеется и это не первый проход по товару, то прибавление всех данных в БД
        if analytics and not self.new_iter:
            analytics.new_price_sum += self.new_price_sum
            analytics.new_count += self.new_count
            analytics.approval_price_sum += self.approval_price_sum
            analytics.approval_count += self.approval_count
            analytics.equipment_price_sum += self.equipment_price_sum
            analytics.equipment_count += self.equipment_count
            analytics.delivery_price_sum += self.delivery_price_sum
            analytics.delivery_count += self.delivery_count
            analytics.point_issue_orders_price_sum += self.point_issue_orders_price_sum
            analytics.point_issue_orders_count += self.point_issue_orders_count
            analytics.canceled_price_sum += self.canceled_price_sum
            analytics.canceled_count += self.canceled_count
            analytics.completed_price_sum += self.completed_price_sum
            analytics.completed_count += self.completed_count
            self.init_count_and_price_sum()
        # TODO Если запись в БД имеется и это первый проход по товару, замена данных на новые
        elif analytics and self.new_iter:
            analytics.new_price_sum = self.new_price_sum
            analytics.new_count = self.new_count
            analytics.approval_price_sum = self.approval_price_sum
            analytics.approval_count = self.approval_count
            analytics.equipment_price_sum = self.equipment_price_sum
            analytics.equipment_count = self.equipment_count
            analytics.delivery_price_sum = self.delivery_price_sum
            analytics.delivery_count = self.delivery_count
            analytics.point_issue_orders_price_sum = self.point_issue_orders_price_sum
            analytics.point_issue_orders_count = self.point_issue_orders_count
            analytics.canceled_price_sum = self.canceled_price_sum
            analytics.canceled_count = self.canceled_count
            analytics.completed_price_sum = self.completed_price_sum
            analytics.completed_count = self.completed_count
        else:
            # TODO Если нет записи в БД, создание этой самой записи
            ProductAnalytics(
                product_id=product['id'],
                category=group_product['name'],
                name=product['name'],
                proportions=proportions_product,
                article=product['article'],
                ordered_count=ordered_count,
                price_sum=price_sum,
                design_method=order_method,
                new_price_sum=self.new_price_sum,
                new_count=self.new_count,
                approval_price_sum=self.approval_price_sum,
                approval_count=self.approval_count,
                equipment_price_sum=self.equipment_price_sum,
                equipment_count=self.equipment_count,
                delivery_price_sum=self.delivery_price_sum,
                delivery_count=self.delivery_count,
                point_issue_orders_price_sum=self.point_issue_orders_price_sum,
                point_issue_orders_count=self.point_issue_orders_count,
                canceled_price_sum=self.canceled_price_sum,
                canceled_count=self.canceled_count,
                completed_price_sum=self.completed_price_sum,
                completed_count=self.completed_count,
                create_date_at=self.date_at,
                create_date_to=self.date_to,
            )

    def parse_product(self):
        """
        Цикл по всем страницам товаров с переходом к перебору всех заказов

        :return:
        """
        page = 1
        stop = 2
        while page <= stop:
            products, stop = self.get_products(page)
            print(f'Страница {page} из {stop} товаров!')
            page += 1
            self.parse_orders(products)
        print('Парсинг закончился!')

    def parse_orders(self, products):
        """
        Перебор всех товаров с получением заказов по каждому товару и переход к получению истории

        :param products: массив товаров для их перебора.
        :return:
        """
        for product in products:
            page = 1
            stop = 2
            # TODO если товар в группе warehouseRoot либо у него нет артикула, идем к следующему товару
            if any([group['externalId'] == 'warehouseRoot' for group in product['groups']]) or \
                    product['article'] == '':
                page += 1
                continue
            # TODO цикл по всем страницам заказов на товар
            while page <= stop:
                orders, stop = self.get_orders(page, product['article'])
                if not orders:
                    continue
                print(f"\033[31m|{product['name']}")
                print(f'\033[33m|Количество заказов - {len(orders)}')
                print(f'\033[37m|Страница {page} из {stop} в заказах!\n'
                      f'----------------------------------------------------------------\n')
                page += 1
                try:
                    self.parse_history(orders, product)
                except Exception:
                    continue

    def parse_history(self, orders, product):
        """
        Перебор всех заказов с получением их истории и дальнейшим расчетом

        :param orders:
        :param product:
        :return:
        """
        for order in orders:
            # TODO получение истории изменений статусов
            history_statuses = [history for history in self.get_history(order['id']) if
                                history['field'] == 'status']
            # TODO если нет истории, переходим к следующему заказу
            if not history_statuses:
                continue
            all_status = self.client.status_groups().get_response()['statusGroups']
            # TODO перебор всей истории заказа и дальнейший расчет
            for history_status in history_statuses:
                try:
                    self.calc_all_history(history_status, all_status, product, order)
                except TypeError:
                    continue

    def get_products(self, page):
        """
        Получение всех товаров со склада

        :param page: страница в товарах(их 8 на данный момент)
        :return:
        """
        products = self.client.products(filters={'name': 'Вейдерсы Finntrail Speedmaster 1528 CamoArmy_N'}, limit=20, page=page).get_response()
        return products['products'], products['pagination']['totalPageCount']

    def get_orders(self, page, article):
        """
        Получение заказов за указанный промежуток времени, в которых на любом этапе присутствовал необходимый товар

        :param page: страница в заказах(если больше 100).
        :param article: артикул товара.
        :return:
        """
        orders = self.client.orders(filters={'product': article, 'createdAtFrom': self.date_at.strftime("%Y-%m-%d"),
                                             'createdAtTo': self.date_to.strftime("%Y-%m-%d")}, limit=20,
                                    page=page).get_response()
        return orders['orders'], orders['pagination']['totalPageCount']

    def get_history(self, order_id):
        """
        Получение истории на конкретный заказ

        :param order_id: внутренний id заказа.
        :return:
        """
        history = self.client.orders_history(filters={'orderId': order_id}, limit=100).get_response()
        return history['history']


if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-da', '--dateAt', help='Дата оформления заказа (от)')
    # parser.add_argument('-dt', '--dateTo', help='Дата оформления заказа (до)')
    # args = parser.parse_args()
    dateAt, dateTo = '2020-03-01', '2021-03-31'
    main = ParserRetailCRM(dateAt, dateTo)
    main.parse_product()
