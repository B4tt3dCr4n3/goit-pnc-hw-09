import argparse
import json
import re

from collections import defaultdict
from sqlalchemy import (Table, Column, Integer, MetaData,
                        select, String, Float, ForeignKey, Date)
from sqlalchemy.dialects import mysql
from common import get_engine, get_default, register_common_cli_params

metadata = MetaData()

customers = Table(
    'customers', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('first_name', String(50)),
    Column('last_name', String(50)),
    Column('email', String(100)),
    Column('phone', String(20)),
    Column('address', String(255))
)

flower_categories = Table(
    'flower_categories', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('category_name', String(50))
)

flowers = Table(
    'flowers', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('category_id', Integer, ForeignKey('flower_categories.id')),
    Column('flower_name', String(100)),
    Column('price', Float),
    Column('stock_quantity', Integer)
)

orders = Table(
    'orders', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('customer_id', Integer, ForeignKey('customers.id')),
    Column('order_date', Date),
    Column('total_amount', Float)
)

transactions = Table(
    'transactions', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('order_id', Integer, ForeignKey('orders.id')),
    Column('transaction_date', Date),
    Column('amount', Float),
    Column('payment_method', String(20))
)

table_map = {
    customers.name: customers,
    flower_categories.name: flower_categories,
    flowers.name: flowers,
    orders.name: orders,
    transactions.name: transactions,
}


def print_data(connection, columns, table=customers):
    """fetch data from database and print to console"""
    default_columns = ['id']
    try:
        if columns:
            table_columns = [table.c.id] + [
                getattr(table.c, i) for i in columns]
            query = select(table_columns)
            extra_columns = columns
        else:
            table_columns = [table.c.id] + [
                i for i in table.columns if i.name not in default_columns]
            query = select(table_columns)
            extra_columns = [
                i.name for i in table.columns if i.name not in default_columns]
    except AttributeError:
        print(
            "\n\n{0}\nprobably you used incorrect column name\n{0}\n\n".format('*' * 30))
        raise
        exit(1)

    print("Fetch data by query {}\n",
          query.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))
    result = connection.execute(query)
    result = result.fetchall()

    print(len(result))
    print("{:<3} - {}".format(*default_columns, ' - '.join(extra_columns)))
    for row in result:
        values = ['{:<3}'.format(row['id'])]
        # for col in row[1:]:
        for col in row._mapping.values():
            if isinstance(col, (bytes, bytearray)):
                values.append(col.decode('utf-8', errors='ignore'))
            else:
                values.append(str(col))

        print(' - '.join(values))


def write_data_from_json(json_string, connection):
    """
    Write data from a JSON file into corresponding tables using SQLAlchemy.

    :param json_file: Path to the JSON file containing data.
    :param connection: Active SQLAlchemy connection object.
    """

    data = json.loads(json_string)
    for table_name, rows in data.items():
        table = table_map.get(table_name)
        if table is None:
            print(f"Table '{table_name}' not found in table map.")
            continue

        if isinstance(rows, dict):  # In case of a single row, wrap it in a list
            rows = [rows]

        for row in rows:
            # Clean and prepare the data for insertion
            clean_row_data = {}
            for column in table.columns:
                col_name = column.name
                if col_name in row:
                    value = row[col_name].strip().strip("'")  # Basic cleaning
                    if isinstance(column.type, Integer):
                        try:
                            clean_row_data[col_name] = int(value)
                        except ValueError:
                            print(f"Invalid integer for '{col_name}': {value}")
                            clean_row_data[col_name] = None
                    elif isinstance(column.type, Float):
                        try:
                            clean_row_data[col_name] = float(value)
                        except ValueError:
                            print(f"Invalid float for '{col_name}': {value}")
                            clean_row_data[col_name] = None
                    else:
                        clean_row_data[col_name] = value

            try:
                connection.execute(table.insert(), clean_row_data)
                print(f"Inserted into '{table_name}': {clean_row_data}")
            except Exception as e:
                print(f"Failed to insert into '{table_name}': {
                      clean_row_data} - Error: {e}")


def extract_insert_commands(sql_dump):
    """Extract all INSERT INTO commands and parse their values into dictionaries."""
    data_for_insertion = []
    insert_pattern = re.compile(
        r"INSERT INTO\s+`?([a-zA-Z0-9_]+)`?\s*\((.*?)\)\s*VALUES\s*(.+?);", re.DOTALL)

    matches = insert_pattern.findall(sql_dump)

    for table, columns, values_block in matches:
        columns = [col.strip('` ')
                   for col in columns.split(',')]  # Clean column names
        values_rows = re.findall(r"\((.*?)\)(?=,|$)", values_block)

        for row in values_rows:
            # Handles quoted strings and numbers
            values = re.findall(r"(?:'(?:[^']|\\')*'|[^',\s]+)", row)
            # Remove quotes from strings
            values = [v.strip("'") for v in values]
            row_dict = dict(zip(columns, values))
            data_for_insertion.append((table, row_dict))

    return data_for_insertion


def convert_to_json(data):
    """
    Convert a list of tuples (table_name, row_data) to a JSON-compatible dictionary.

    :param data: List of tuples [(table_name, row_data_dict)].
    :return: JSON string representation of the grouped data.
    """
    grouped_data = defaultdict(
        list)  # Create a dictionary with lists as default values

    for table_name, row_data in data:
        grouped_data[table_name].append(row_data)  # Group rows by table name

    # Convert the grouped data dictionary to a JSON string
    json_data = json.dumps(grouped_data, indent=4)
    return json_data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    register_common_cli_params(parser)
    parser.add_argument('--data', type=str,
                        default=get_default('data', ''),
                        help='data to save in ascii. default random data')
    parser.add_argument('-c', '--columns', nargs='+', dest='columns',
                        default=get_default('columns', False), help='List of columns to display')
    parser.add_argument('--db_table', default=customers.name,
                        help='Table used to read/write data')
    parser.add_argument('--import_dump', type=str,
                        help='Path to SQL dump file for import data from it')
    args = parser.parse_args()

    engine = get_engine(
        db_host=args.host, db_port=args.port, db_user=args.db_user, db_password=args.db_password,
        db_name=args.db_name, is_mysql=args.mysql, is_postgresql=args.postgresql,
        tls_ca=args.tls_root_cert, tls_key=args.tls_key, tls_crt=args.tls_cert,
        sslmode=args.ssl_mode, verbose=args.verbose)
    connection = engine.connect()
    metadata.create_all(engine)

    if args.import_dump:
        with open(args.import_dump, 'r', encoding="utf-8") as file:
            sql_dump = file.read()
        insert_data = extract_insert_commands(sql_dump)
        json_data = convert_to_json(insert_data)
        write_data_from_json(json_data, connection)
    elif args.print:
        print_data(connection, args.columns, table_map[args.db_table])
    else:
        print('Use --print or --data options')
        exit(1)
