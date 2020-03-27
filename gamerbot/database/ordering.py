#!/usr/bin/env python

# Copyright (c) 2020 Matt Struble. All Rights Reserved.
#
# Use is subject to license terms.
#
# Author: Matt Struble
# Date: Mar. 18 2020

class _Ordering(object):
    max_order_size = 3

    sql = "ORDER BY"

    def __init__(self, database, orders):
        self.orders = orders
        self.database = database

    def __repr__(self):
        return self.sql

    def __str__(self):
        return self.sql

    def _verify_orders(self):
        for order in self.orders:
            if type(order) is not tuple and type(order) is not list:
                raise ValueError("Unexpected order ['{}'] expected tuple or list".format(order))

            if len(order) > _Ordering.max_order_size:
                raise ValueError(
                    "Unexpected length to order ['{}'] max length should be {}".format(order, _Ordering.max_order_size))

            # first component in order should be column
            self.database._validate_column(order[0])
            self._validate_ordering(order[1:])

    @staticmethod
    def _validate_ordering(orders):
        for component in orders:
            if not isinstance(component, type) or not issubclass(component, _Ordering):
                raise ValueError("Unexpected ordering component ['{}']".format(component))

    @staticmethod
    def _order_to_string(order):
        ret_str = order[0]

        for component in order[1:]:
            ret_str += " {}".format(component.sql)

        return ret_str

    def to_sql(self):
        self._verify_orders()

        if len(self.orders) == 0:
            return ""

        ret_sql = " {} {}".format(self.sql, self._order_to_string(self.orders[0]))

        for order in self.orders[1:]:
            ret_sql += ", {}".format(self._order_to_string(order))

        return ret_sql


class Asc(_Ordering):
    sql = "ASC"


class Desc(_Ordering):
    sql = "DESC"


class NullsFirst(_Ordering):
    sql = "NULLS FIRST"


class NullsLast(_Ordering):
    sql = "NULLS LAST"
