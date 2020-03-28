#!/usr/bin/env python

# Copyright (c) 2020 Matt Struble. All Rights Reserved.
#
# Use is subject to license terms.
#
# Author: Matt Struble
# Date: Feb. 17 2020
from .ordering import _Ordering


class Result(object):
    def __init__(self, table, values, return_columns):
        self.__name__ = table.name + "_result"

        self.dict = {}

        for i in range(len(return_columns)):
            c = return_columns[i]
            v = values[i]
            self.dict[c] = v
            setattr(self, c, v)

    def __repr__(self):
        return str(self.dict)

    def __getitem__(self, item):
        return self.dict[item]

    def __len__(self):
        return len(self.dict)


class Database(object):
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()
        self.table = None
        self.sql = ""
        self.values = {}

    def selectFrom(self, table):
        select = _SelectDatabase(self.connection, "*")
        select = select.FROM(table)
        return select

    def select(self, *selections):
        return _SelectDatabase(self.connection, selections)

    def insertInto(self, table, *columns):
        return _InsertDatabase(self.connection, table, columns)

    def execute(self):
        if len(self.values) > 0:
            self.cursor.execute(self.sql, self.values)
        else:
            self.cursor.execute(self.sql)

    def _validate_column(self, column):
        if column not in self.table.columns:
            raise ValueError("Unexpected column ['{}'] for table ['{}']".format(column, self.table.name))


class _FetchableDatabase(Database):
    def __init__(self, connection):
        super().__init__(connection)
        self.return_columns = []

    def fetchone(self):
        self.execute()
        return self._convert_to_result(self.cursor.fetchone())

    def fetchmany(self, size):
        if not isinstance(size, int):
            raise ValueError("Size needs to be an integer.")

        self.execute()
        return self._convert_to_result(self.cursor.fetchmany(size))

    def fetchall(self):
        self.execute()
        return self._convert_to_result(self.cursor.fetchall())

    def orderBy(self, *orderings):
        self.sql += _Ordering(self, orderings).to_sql()
        return self

    def _gen_result(self, value):
        if len(self.return_columns) == 1:
            return value[0]
        else:
            return Result(self.table, value, self.return_columns)

    def _convert_to_result(self, value):
        if value is None:
            return value

        if type(value) is tuple:
            return self._gen_result(value)
        else:
            results = []
            for r in value:
                results.append(self._gen_result(r))
            return results


class _SelectDatabase(_FetchableDatabase):
    def __init__(self, connection, selections):
        super().__init__(connection)

        if len(selections) == 0:
            raise ValueError("Selections needs to be a string with len > 0 or an array of len > 0")

        self.return_columns = selections

    def FROM(self, table):
        self.table = table

        self.sql = "SELECT {} FROM \"{}\"".format(','.join(self.return_columns), table.name)

        if self.return_columns is '*':
            self.return_columns = self.table.columns

        for column in self.return_columns:
            self._validate_column(column)

        return self

    def _validate_conditional(self, conditional):
        self._validate_column(conditional.column)

    def _construct_logical_sql(self, operator, conditional):
        self._validate_conditional(conditional)

        if conditional.has_value:
            value_name = conditional.name + str(len(self.values))
            self.values[value_name] = conditional.value

            # https://www.psycopg.org/docs/usage.html#query-parameters
            self.sql += " {} \"{}\".\"{}\" {} %({})s".format(operator, self.table.name, conditional.column, conditional.conditional, value_name)
        else:
            self.sql += " {} \"{}\".\"{}\" {}".format(operator, self.table.name, conditional.column, conditional.conditional)

    def WHERE(self, conditional):
        self._construct_logical_sql('WHERE', conditional)
        return self

    def AND(self, conditional):
        self._construct_logical_sql('AND', conditional)
        return self

    def OR(self, conditional):
        self._construct_logical_sql('OR', conditional)
        return self

class _ReturningDatabase(_FetchableDatabase):
    def __init__(self, connection, table, sql, returning):
        super().__init__(connection)
        self.table = table

        if len(returning) == 0:
            raise ValueError("Returning columns need to contain at least one value.")

        for column in returning:
            self._validate_column(column)

        self.sql = sql + " RETURNING {}".format(','.join(returning))
        self.return_columns = returning

class _InsertDatabase(Database):
    def __init__(self, connection, table, insert_columns):
        super().__init__(connection)

        if len(insert_columns) == 0:
            raise ValueError("Insert columns need to contain at least one value.")

        self.table = table
        self.insert_columns = insert_columns
        self.inserts = []

        self.value_placeholder = "({})".format(','.join(['%s']*len(insert_columns)))

        for column in self.insert_columns:
            self._validate_column(column)

        self.sql = "INSERT INTO \"{}\" ({}) VALUES ".format(table.name, ','.join('"{}"'.format(c) for c in insert_columns))

    def _build_mogrifies(self):
        mogrifies = (self.cursor.mogrify(self.value_placeholder, tuple(x)) for x in self.inserts)
        arg_str = b','.join(mogrifies)

        self.sql += arg_str.decode("utf-8")

    def _validate_sql(self):
        if len(self.inserts) == 0:
            raise ValueError("No values were prepared for insert. Invalid SQL statement created.")

    def prepare(self, *args):
        if len(args) != len(self.insert_columns):
            raise ValueError("Provided list of arguments length [{}] does not match expected columns length [{}].".format(args, self.insert_columns))

        self.inserts.append(args)

        return self

    def execute(self):
        self._validate_sql()
        self._build_mogrifies()
        super().execute()

    def returning(self, *returning):
        self._validate_sql()
        self._build_mogrifies()

        return _ReturningDatabase(self.connection, self.table, self.sql, returning)