#!/usr/bin/env python

# Copyright (c) 2020 Matt Struble. All Rights Reserved.
#
# Use is subject to license terms.
#
# Author: Matt Struble
# Date: Feb. 17 2020


class _Conditional(object):
    def __init__(self, column, value):
        self.column = column
        self.value = value
        self.name = ""
        self.conditional = ""
        self.has_value = True

    def negate(self):
        return "NOT " + self.conditional


class Like(_Conditional):
    def __init__(self, column, value):
        super().__init__(column, value)
        self.name = "like"
        self.conditional = "LIKE"


class Eq(_Conditional):
    def __init__(self, column, value):
        super().__init__(column, value)
        self.name = "eq"
        self.conditional = "="

    def negate(self):
        return "!="


class In(_Conditional):
    def __init__(self, column, value):
        super().__init__(column, value)
        # psycopg2 expects tuples instead of arrays for IN modifier, convert now for ease of use later
        self.value = tuple(value)
        self.name = "in"
        self.conditional = "IN"


class Is(_Conditional):
    def __init__(self, column, value):
        super().__init__(column, value)
        self.conditional = "IS"
        self.name = "is"

    def negate(self):
        return "IS NOT"


class IsNull(Is):
    def __init__(self, column):
        super().__init__(column, None)
        self.has_value = False
        self.conditional = "IS NULL"
        self.name = "isNull"

    def negate(self):
        return "IS NOT NULL"


class Not(_Conditional):
    def __init__(self, conditional):
        super().__init__(conditional.column, conditional.value)

        self.conditional = conditional.negate()
        self.name = "not" + conditional.name
        self.has_value = conditional.has_value