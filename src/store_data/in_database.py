import psycopg2
import yaml

class Database():
    def __init__(self):
        with open('../config.yaml') as f:
             db_url = yaml.load(f, Loader=yaml.FullLoader)['POSTGRESQL_URL']

        self.db = psycopg2.connect(db_url, sslmode='require')
        self.cursor =self.db.cursor()

    def __del__(self):
        self.db.close()
        self.cursor.close()

    def execute(self, query, args={}):
        self.cursor.execute(query, args)
        row = self.cursor.fetchall()
        return row

    def commit(self):
        self.cursor.commit()

class Query(Database):
    def create_schema(self, schema_name):
        sql = f"CREATE SCHEMA {schema_name}"
        try:
            self.cursor.execute(sql)
            self.db.commit()
        except Exception as e:
            print("schema 생성 중 오류가 있습니다 : ", e)

    def create_table(self, schema_name, table_name, col_name_list, col_type_list):
        sql = f"CREATE TABLE {schema_name}.{table_name} ("

    def insert_data(self, schema, table, column, data):
        sql = f"INSERT INTO {schema}.{table}({column}) VALUES ('{data}');"
        try:
            self.cursor.execute(sql)
            self.db.commit()
        except Exception as e:
            print("insert 중 오류가 있습니다 : ", e)

    def read_data(self, schema, table, column):
        sql = f"SELECT {column} FROM {schema}.{table};"
        try:
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
        except Exception as e:
            result = ("read 중 오류가 있습니다 : ", e)

        return result

    def update_data(self, schema, table, column, value, condition):
        sql = f"UPDATE {schema}.{table} SET {column}='{value}' WHERE {column}='{condition};'"
        try:
            self.cursor.execute(sql)
            self.db.commit()
        except Exception as e:
            print("update 중 오류가 있습니다 : ", e)

    def delete_data(self, schema, table, condition):
        sql = f"DELETE FROM {schema}.{table} WHERE {condition};"
        try:
            self.cursor.execute(sql)
            self.db.commit()
        except Exception as e:
            print("delete DB err", e)