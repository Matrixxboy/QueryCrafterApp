import sys
import json
import os
import mysql.connector
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt
from Settings.Setting import SettingsPage


class QueryCrafterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧠 QueryCrafter - SQL Assistant")
        self.setFixedSize(900, 600)

        self.connection = None
        self.cursor = None

        self.init_ui()
        self.connect_to_database()

    # ------------------ UI Layout ------------------
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # --- Query Input Area ---
        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("Write or paste your SQL query here...")
        self.query_input.setStyleSheet("""
            QTextEdit {
                background-color: #2f2f2f;
                color: #f0f0f0;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.query_input)

        # --- Buttons ---
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("▶️ Run Query")
        self.db_structure_btn = QPushButton("Show DB Structure")
        self.clear_btn = QPushButton("🧹 Clear")
        self.settings_btn = QPushButton("⚙️ Settings")
        self.exit_btn = QPushButton("❌ Exit")

        for btn in [self.run_btn, self.db_structure_btn, self.clear_btn, self.settings_btn, self.exit_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #555;
                    color: #fff;
                    border-radius: 6px;
                    padding: 6px 12px;
                }
                QPushButton:hover { background-color: #666; }
            """)

        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.db_structure_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.settings_btn)
        btn_layout.addWidget(self.exit_btn)
        layout.addLayout(btn_layout)
        
        # --- Results Table ---
        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #3c3c3c;
                color: #f0f0f0;
                border: 1px solid #555;
                gridline-color: #666;
            }
            QHeaderView::section {
                background-color: #2e2e2e;
                color: #fff;
                border: 1px solid #555;
            }
        """)
        layout.addWidget(self.table)

        # --- Button Connections ---
        self.run_btn.clicked.connect(self.execute_query)
        self.db_structure_btn.clicked.connect(self.show_db_structure)
        self.clear_btn.clicked.connect(self.clear_query)
        self.settings_btn.clicked.connect(self.open_settings)
        self.exit_btn.clicked.connect(self.close_app)

    # ------------------ DB Connection ------------------
    def connect_to_database(self):
        settings_path = os.path.join(os.path.dirname(__file__), "SavedData", "db_settings.json")
        if not os.path.exists(settings_path):
            QMessageBox.warning(self, "Settings Missing", "⚠️ Database settings not found! Open Settings first.")
            return

        try:
            with open(settings_path, "r") as f:
                data = json.load(f)

            self.connection = mysql.connector.connect(
                host=data["host"],
                user=data["user"],
                password=data["password"],
                database=data["database"]
            )
            self.cursor = self.connection.cursor()
            QMessageBox.information(self, "Connected", "✅ Database connected successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"❌ Failed to connect:\n{e}")

    # ------------------ Execute Query ------------------
    def execute_query(self):
        if not self.connection or not self.cursor:
            QMessageBox.warning(self, "Not Connected", "⚠️ No active database connection.")
            return

        query = self.query_input.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "Empty Query", "⚠️ Please enter a SQL query.")
            return

        try:
            self.cursor.execute(query)

            if self.cursor.with_rows:
                rows = self.cursor.fetchall()
                columns = [desc[0] for desc in self.cursor.description]
                self.show_results(columns, rows)
                QMessageBox.information(self, "Success", f"✅ {len(rows)} rows fetched.")
            else:
                self.connection.commit()
                QMessageBox.information(self, "Executed", "✅ Query executed successfully (no data returned).")

        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Query Error", f"⚠️ {err}")

    # ------------------ Show DB Structure ------------------
    def show_db_structure(self):
        if not self.connection or not self.cursor:
            QMessageBox.warning(self, "Not Connected", "⚠️ No active database connection.")
            return

        try:
            # Get the current database name
            self.cursor.execute("SELECT DATABASE()")
            db_name = self.cursor.fetchone()[0]

            # Get all tables in the database
            self.cursor.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{db_name}'")
            tables = self.cursor.fetchall()

            if not tables:
                QMessageBox.information(self, "No Tables", "No tables found in the current database.")
                return

            all_table_structures = []
            for table in tables:
                table_name = table[0]
                self.cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = '{db_name}' AND table_name = '{table_name}'")
                columns = self.cursor.fetchall()
                all_table_structures.append((table_name, columns))

            self.table.clear()
            self.table.setColumnCount(3)
            self.table.setHorizontalHeaderLabels(["Table Name", "Column Name", "Data Type"])
            
            row_position = 0
            for table_name, columns in all_table_structures:
                for i, (column_name, data_type) in enumerate(columns):
                    self.table.insertRow(row_position)
                    if i == 0:
                        self.table.setItem(row_position, 0, QTableWidgetItem(table_name))
                    self.table.setItem(row_position, 1, QTableWidgetItem(column_name))
                    self.table.setItem(row_position, 2, QTableWidgetItem(data_type))
                    row_position += 1
            
            self.table.resizeColumnsToContents()
            try:
                with open(os.path.join(os.path.dirname(__file__), "SavedData/db_structure.json"), "w", encoding="utf-8") as f:
                    json.dump(all_table_structures, f, ensure_ascii=False, separators=(',', ':'))
            except Exception as e:  
                    QMessageBox.information(self, "Error", f"⚠️ {e}")
            QMessageBox.information(self, "Success", "✅ Database structure loaded.")

        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Error", f"⚠️ {err}")
    # ------------------ Prompt Function ------------------
    def prompt(self, question):
        db_name = self.cursor.fetchone()[0]
        with open(os.path.join(os.path.dirname(__file__), "../SavedData/db_structure.json"), "r", encoding="utf-8") as f:
            data = json.load(f)

        promt=f"""Youre are the professional SQL Builder
        name of the datbase is {db_name}  
        structure of the database is {data}
        please make query as this {question} """
        
    # ------------------ Display Results ------------------
    def show_results(self, columns, rows):
        self.table.clear()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setRowCount(len(rows))

        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))

        self.table.resizeColumnsToContents()

    # ------------------ Utility Methods ------------------
    def clear_query(self):
        self.query_input.clear()
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

    def open_settings(self):
        self.settings_window = SettingsPage()
        self.settings_window.show()

    def close_app(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
        self.close()


# ------------------ Run the App ------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QueryCrafterApp()
    window.show()
    sys.exit(app.exec())