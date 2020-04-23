import mysql.connector, sys, configparser, datetime
from mysql.connector import errorcode
from collections import OrderedDict

class MysqlPython(object):
    __instance   = None
    __host       = None
    __user       = None
    __password   = None
    __database   = None
    __session    = None
    __connection = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance or not cls.__database:
             cls.__instance = super(MysqlPython, cls).__new__(cls,*args,**kwargs)
        return cls.__instance
    ## End def __new__

    def __init__(self,cnfg='mysql2'):
        self.filename = 'config.ini'
        self.config = configparser.ConfigParser()
        self.config.read(self.filename)
        self.configuration=self.config[cnfg]
        self.__host     = self.configuration['MYSQL_HOST']
        self.__user     = self.configuration['MYSQL_USER']
        self.__password = self.configuration['MYSQL_PASS']
        self.__database = self.configuration['MYSQL_DB']
    ## End def __init__
    

    def __open(self):
        try:
            cnx = mysql.connector.connect(user=self.__user, password=self.__password, host=self.__host, database=self.__database)
            #cnx = MySQLdb.connect(self.__host, self.__user, self.__password, self.__database)
            self.__connection = cnx
            self.__session    = cnx.cursor()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
    ## End def __open


    def __close(self):
        self.__session.close()
        self.__connection.close()
    ## End def __close


    def select(self, table, where=None, *args, **kwargs):
        result = None
        query = 'SELECT '
        keys = args
        values = tuple(kwargs.values())
        l = len(keys) - 1

        for i, key in enumerate(keys):
            query += "`"+key+"`"
            if i < l:
                query += ","
        ## End for keys

        query += ' FROM %s' % table

        if where:
            query += " WHERE %s" % where
        ## End if where

        print(query)

        self.__open()
        self.__session.execute(query, values)
        number_columns = len(self.__session.description)
        records = self.__session.fetchall()
        number_rows = self.__session.rowcount

        if number_rows >= 1 and number_columns > 1:
            result = [item for item in records]
        else:
            result = [item[0] for item in records]
        self.__connection.commit()
        self.__close()

        return result
    ## End def select


    def select_custom(self, sql):
        self.__open()
        self.__session.execute(sql)
        number_columns = len(self.__session.description)
        records = self.__session.fetchall()
        number_rows = self.__session.rowcount
        if number_rows >= 1 and number_columns > 1:
            result = [item for item in records]
        else:
            result = [item[0] for item in records]
        self.__connection.commit()
        self.__close()
        return result


    def update(self, table, where=None, *args, **kwargs):
        query  = "UPDATE %s SET " % table
        keys   = kwargs.keys()
        values = tuple(kwargs.values()) + tuple(args)
        l = len(keys) - 1
        for i, key in enumerate(keys):
            query += "`"+key+"` = %s"
            if i < l:
                query += ","
            ## End if i less than 1
        ## End for keys
        query += " WHERE %s" % where

        self.__open()
        self.__session.execute(query, values)
        self.__connection.commit()

        # Obtain rows affected
        update_rows = self.__session.rowcount
        self.__close()

        return update_rows
    ## End function update

    def insert(self, table, *args, **kwargs):
        values = None
        query = "INSERT INTO %s " % table
        if kwargs:
            keys = kwargs.keys()
            values = tuple(kwargs.values())
            query += "(" + ",".join(["`%s`"] * len(keys)) %  tuple (keys) + ") VALUES (" + ",".join(["%s"]*len(values)) + ")"
        elif args:
            values = args
            query += " VALUES(" + ",".join(["%s"]*len(values)) + ")"

        self.__open()
        self.__session.execute(query, values)
        self.__connection.commit()
        self.__close()
        return self.__session.lastrowid
    ## End def insert

    def insert_advanced(self, sql):
        self.__open()
        self.__session.execute(sql)
        self.__connection.commit()
        self.__close()
        return "Success"

    def delete(self, table, where=None, *args):
        query = "DELETE FROM %s" % table
        if where:
            query += ' WHERE %s' % where

        values = tuple(args)

        self.__open()
        self.__session.execute(query, values)
        self.__connection.commit()

        # Obtain rows affected
        delete_rows = self.__session.rowcount
        self.__close()

        return delete_rows
    ## End def delete

    def select_advanced(self, sql, *args):
        od = OrderedDict(args)
        query  = sql
        values = tuple(od.values())
        self.__open()
        self.__session.execute(query, values)
        number_columns = len(self.__session.description)
        records = self.__session.fetchall()
        number_rows = self.__session.rowcount

        if number_rows >= 1 and number_columns > 1:
            result = [item for item in records]
        else:
            result = [item[0] for item in records]

        self.__connection.commit()
        self.__close()
        return result
    ## End def select_advanced
## End class

#################################
#============ USAGE =============
#################################
# Usage
# To start using the Python MySQL class you need to import the class and initialize with config.ini parameter: 'mysql2'

# from mysqlDB.database import MysqlPython
# connect_mysql = MysqlPython('mysql2')


# Select one condition
# If you want to obtain information from one table and use one condition, you could use select function where args argument is for referencing the columns you need to obtain.
#   conditional_query = 'car_make = %s '
#   result = connect_mysql.select('car', conditional_query, 'id_car', 'car_text', car_make='nissan')
# Result: The function return a list or empty list in case of not find nothing.


# Select more than one condition
# In case you have need to obtain information with more than one condition, you could use the select_advancedfunction, where the columns you need to obtain are referenced by args and the conditionals are referenced by tuples
#   sql_query = 'SELECT C.cylinder FROM car C WHERE C.car_make = %s AND C.car_model = %s'
#   result = connect_mysql.select_advanced(sql_query, ('car_make', 'nissan'),('car_model','altima'))
# Note: Inside the sql_advanced function the order of the parameters matters, so the tuples should have the order of the query.
# Result: The function return a list or empty list in case of not find nothing.


# Insert data
# Inserting data is really simple and intuitive, where we are going to reference the column and the values
#   result = connect_msyql.insert('car', car_make='ford', car_model='escort', car_year='2005')
# Result: The function return the last row id was inserted.


# Update data
# To update data just needs the table, conditional query and specify the columns you want update
# conditional_query = 'car_make = %s'
# result = connect_mysql.update('car_table', conditional_query, 'nissan', car_model='escort', car_year='2005')
# Result: This function return the amount of rows updated.


# Delete data
# Delete data is really simple like insert, just reference the column as condition and table.
#   conditional_query = 'car_make = %s'
#   result = connect_mysql.delete('car', conditional_query, 'nissan')
# Result: This function return the amount of rows deleted.

# from mysqlDB.database import MysqlPython

# connect_mysql = MysqlPython()

# # Select on one condition
# conditional_query = 'ID > %s '%(1)
# result = connect_mysql.select('df_cb_log', conditional_query, 'ID', 'CREATED_AT', 'MESSAGE_BY')
# print(result)

# # Insert Query
# result = connect_mysql.insert('df_cb_log', MESSAGE_BY='Bot', LOG_MESSAGE='Test Message', USER_NAME='Piyush Jain')
# print(result) #Return ID Number