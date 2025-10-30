import os
import json
import mysql.connector
from sqlalchemy import create_engine, inspect , exc

class DatabaseManager:
    def __init__(self, port, host, user, password, database):
        try:
            self.conn = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            self.cursor = self.conn.cursor()
            print("✅ Database connected.")

            try:
                engine = create_engine(
                    f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
                )
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                self.db_structure = {}

                for table in tables:
                    columns = inspector.get_columns(table)
                    self.db_structure[table] = [
                        {
                            "name": col["name"],
                            "type": str(col["type"]),
                            "nullable": col["nullable"],
                            "default": col["default"],
                            "primary_key": col["primary_key"],
                        }
                        for col in columns
                    ]

                print("🔍 Preparing to write DB structure to file...")
                filename = os.path.join(os.path.dirname(__file__), "db_structure.json")

                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(self.db_structure, f, indent=4)

                print(f"✅ Data successfully written to {filename}")

            except exc.SQLAlchemyError as e:
                print(f"⚠️ Error while fetching database structure: {e}")
                self.db_structure = None

        except mysql.connector.Error as err:
            print(f"❌ Database connection error: {err}")
            self.conn = None
            self.cursor = None
            self.db_structure = None
    
    def get_db_structure(self):
        return self.db_structure


    def execute_query(self, query):
        if not self.conn or not self.cursor:
            print("⚠️ No active database connection.")
            return None

        try:
            self.cursor.execute(query)

            # Check if the query returns data (like SELECT)
            if self.cursor.with_rows:
                rows = self.cursor.fetchall()
                columns = [desc[0] for desc in self.cursor.description]
                print("✅ Query executed successfully.")
                print("Columns:", columns)
                print("Rows:", rows)
                return columns, rows
            else:
                self.conn.commit()  # For INSERT, UPDATE, DELETE
                print("✅ Query executed successfully (no data to fetch).")
                return None, None

        except mysql.connector.Error as err:
            print(f"⚠️ Query error: {err}")
            return None, None

    def close(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn and self.conn.is_connected():
                self.conn.close()
            print("🔒 MySQL connection closed.")
        except Exception as e:
            print(f"⚠️ Error while closing connection: {e}")
