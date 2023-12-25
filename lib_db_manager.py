import sys, os, configparser, psycopg2, psycopg2.extras as extras


def db_connection(db_connection_string):
    #  creates connection to database
    print(db_connection_string)
    print('connecting to database ..... ', end='')
    try:
        conn = psycopg2.connect(db_connection_string)  # postgre database
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


def db_insert_data(conn, cursor, data_set, table, columns):
    #  inserts data_set into database
    print('inserting data set to database ..... ', end='')
    try:
        #  insert actions for Postgre database
        query_insert_data = "insert into %s(%s) values %%s" % (table, columns)
        extras.execute_values(cursor, query_insert_data, data_set)
        conn.commit()        
        print('ok')
    except(Exception) as err:
        print('error'); print(err)
        conn.rollback()
        sys.exit() 


def db_execute(conn, cursor, query):
    #  delete and update commands
    print('deleting data from database ..... ', end='')
    try:
        cursor.execute(query)
        conn.commit()        
        print('ok')
    except(Exception) as err:
        print('error'); print(err)
        conn.rollback()
        sys.exit() 

# query = f'select * from {DB_TABLE}'
# conn, cursor = db_connection(DB_CONNECTION_STRING)
# db_read_data(cursor, query)

# data_set = [('The left hand of darkness', 'Ursule Le Guin', '', '@omalit283'), ]
# columns = 'title, author, photo, book_owner'
# db_insert_data(conn, cursor, data_set, DB_TABLE, columns)
