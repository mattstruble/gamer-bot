#!/usr/bin/env python

# Copyright (c) 2020 Matt Struble. All Rights Reserved.
#
# Use is subject to license terms.
#
# Author: Matt Struble
# Date: Mar. 18 2020
from .conditionals import Eq, IsNull


def fetchone_from_table(database, table, values_dict, returning):
    """
    Constructs a generic fetchone database command from a generic table with provided table_column:value_dictionary mapping.

    Mostly used for other helper functions.

    :param database: Current active database connection.
    :param table: Table to insert mapping into.
    :param values_dict: A dictionary of table_column:value to ingest into the database.
    :param returning: A single column, or list of columns, you want returned.
    :return: The row in the database filtered on the column(s) defined.
    """
    columns = list(values_dict.keys())

    if type(returning) is not list and type(returning) is not tuple:
        returning = [returning]

    db = database.select(*returning).FROM(table).WHERE(Eq(columns[0], values_dict[columns[0]]))

    for column in columns[1:]:
        if values_dict[column] is not None:
            db = db.AND(Eq(column, values_dict[column]))
        else:
            db = db.AND(IsNull(column))

    return db.fetchone()


def ingest_if_not_exist_returning(database, table, values_dict, returning_columns):
    """
    Ingests a table_column:value dictionary mapping into a single row of the database,
    if a matching row doesn't already exist, and returns a filtered result.

    :param database: Current active database connection.
    :param table: Table to insert mapping into.
    :param values_dict: A dictionary of table_column:value to ingest into the database.
    :param returning_columns: A single column, or list of columns, you want returned.
    :return: The row in the database filtered on the column(s) defined.
    """
    columns = list(values_dict.keys())
    values = list(values_dict.values())

    result = fetchone_from_table(database, table, values_dict, returning_columns)

    if result is None:
        result = database.insertInto(table, *columns).prepare(*values).returning(*returning_columns).fetchone()

    return result


def ingest_if_not_exist(database, table, values_dict):
    """
    Ingests a table_column:value dictionary mapping into a single row of the database, if a matching row doesn't already exist.

    :param database: Current active database connection.
    :param table: Table to insert mapping into.
    :param values_dict: A dictionary of table_column:value to ingest into the database.
    """
    columns = list(values_dict.keys())
    values = list(values_dict.values())

    result = fetchone_from_table(database, table, values_dict, table.columns)

    if result is None:
        database.insertInto(table, *columns).prepare(*values).execute()

