import sys, os, configparser, psycopg2, psycopg2.extras as extras, pyodbc
import sqlite3

import os, configparser
from pathlib import Path

config = configparser.ConfigParser()
config_file = os.path.join(Path(__file__).resolve().parent, 'config.ini')   
if os.path.exists(config_file):
  config.read(config_file, encoding='utf-8')
else:
  print("error! config file doesn't exist"); sys.exit()
TOKEN = config['bot']['bot_token']
DB_TYPE = config['db']['db_type']
DB_CONNECTION_STRING = config['db']['db_connection_string']
DB_USER = config['db']['db_user']
DB_PASSWORD = config['db']['db_password']
DB_TABLE = config['db']['db_table']
if DB_TYPE == '-m' and 'DSN' in DB_CONNECTION_STRING:
  DB_CONNECTION_STRING += (';UID='+DB_USER+';PWD='+DB_PASSWORD)


def db_connection(db_connection_string, db_type):
    #  creates connection to database
    print(db_connection_string)
    print('connecting to database ..... ', end='')
    try:
        if db_type == '-p':
            conn = psycopg2.connect(db_connection_string)  # postgre database
        elif db_type == '-m':
            conn = pyodbc.connect(db_connection_string)     # ms-sql database
        elif db_type == '-s':
            conn = sqlite3.connect(db_connection_string)
        cursor = conn.cursor()
        print('ok')
    except(Exception) as err:
        print('error database connection'); print(err)
        sys.exit()

    return conn, cursor


def db_read_data(cursor, query):
    #  loads data from db1
    print('retrieving data ..... ', end='')
    try:
        cursor.execute(query)
        data_set = cursor.fetchall()  # список кортежей
        print('ok ' + f'retrieved [{len(data_set)}] rows')
    except(Exception) as err:
        print('error'); print(err)
        sys.exit()

    return data_set


def db_insert_data(conn, cursor, data_set, db_type, table, columns):
    #  inserts data_set into database
    print('inserting data set to database ..... ', end='')
    try:
        if db_type == '-p':
            #  insert actions for Postgre database
            query_insert_data = "insert into %s(%s) values %%s" % (table, columns)
            extras.execute_values(cursor, query_insert_data, data_set)
            conn.commit()  
        
        elif db_type in ['-m', '-s']:
            #  insert actions for MS-SQL or SQLITE database
            q_str = str()
            for i in range(len(columns.split(','))):
                q_str += '?,'
            q_str = q_str[:-1]
            query_insert_data = f'insert into {table} ({columns}) values ({q_str})'
            cursor.executemany(query_insert_data, data_set)   
            conn.commit()           

        print('ok')

    except(Exception) as err:
        print('error'); print(err)
        conn.rollback()
        sys.exit() 


def db_execute(conn, cursor, query):
    #  delete and update commands
    print('execute ..... ', end='')
    try:
        cursor.execute(query)
        conn.commit()        
        print('ok')
    except(Exception) as err:
        print('error'); print(err)
        conn.rollback()
        sys.exit() 

def first_run_create_table(conn, cursor, db_type):
    #
    if db_type == '-s':
        query = f"""
            create table if not exists {DB_TABLE} (	
                id integer primary key,
                title text not null,
                author text not null,
                photo text not null,
                book_owner text not null,
                create_date text default current_timestamp not null,
                update_date text default null
            )
        """
        db_execute(conn, cursor, query)






#*********************
# query = f'select * from {DB_TABLE}'
# conn, cursor = db_connection(DB_CONNECTION_STRING, DB_TYPE)
# db_execute(conn, cursor, 'drop table books_catalog')
# first_run_create_table(cursor, DB_TYPE)
#print(db_read_data(cursor, query))

# data_set = [('The left hand of darkness', 'Ursule Le Guin', '', '@omalit283'), ]
# columns = 'title, author, photo, book_owner'
# db_insert_data(conn, cursor, data_set, DB_TYPE, DB_TABLE, columns)

# db_read_data(cursor, query)
