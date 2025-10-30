import os
import json
import mysql.connector
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLineEdit, QPushButton,
    QVBoxLayout, QFormLayout, QMessageBox
)

from Databases.MySQL.connection import DatabaseManager

# --- Change starts here ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "..", "SavedData")  # one folder up, then SavedData
os.makedirs(SAVE_DIR, exist_ok=True)  # Create folder if not exists

SETTINGS_FILE = os.path.join(SAVE_DIR, "db_settings.json")

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚙️ Database Settings")
        self.setFixedSize(400, 300)
        self.setStyleSheet("""
            QWidget {
                background-color: #2e2e2e;
                color: #f0f0f0;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px;
                color: #fff;
            }
            QPushButton {
                background-color: #555;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)

        # --- Form Fields ---
        self.host_input = QLineEdit()
        self.port_input = QLineEdit()
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.db_input = QLineEdit()

        # Load saved settings
        self.load_settings()

        # --- Buttons ---
        self.test_btn = QPushButton("🔍 Test Connection")
        self.save_btn = QPushButton("💾 Save Settings")

        self.test_btn.clicked.connect(self.test_connection)
        self.save_btn.clicked.connect(self.save_settings)

        # --- Layout ---
        form = QFormLayout()
        form.addRow("Host:", self.host_input)
        form.addRow("Port:", self.port_input)
        form.addRow("User:", self.user_input)
        form.addRow("Password:", self.pass_input)
        form.addRow("Database:", self.db_input)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.test_btn)
        layout.addWidget(self.save_btn)
        self.setLayout(layout)

    # 🧠 Load from JSON
    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                self.host_input.setText(data.get("host", ""))
                self.port_input.setText(data.get("port", "3306"))
                self.user_input.setText(data.get("user", ""))
                self.pass_input.setText(data.get("password", ""))
                self.db_input.setText(data.get("database", ""))

    # 💾 Save to JSON
    def save_settings(self):
        data = {
            "host": self.host_input.text(),
            "user": self.user_input.text(),
            "port": self.port_input.text(),
            "password": self.pass_input.text(),
            "database": self.db_input.text(),
        }
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=4)
        QMessageBox.information(self, "Saved", "✅ Settings saved successfully!")

    # 🔍 Test MySQL Connection
    def test_connection(self):
        try:
            conn = DatabaseManager(
                host=self.host_input.text(),
                port=int(self.port_input.text()),
                user=self.user_input.text(),
                password=self.pass_input.text(),
                database=self.db_input.text()
            )
            if conn:
                print("✅ Connection successful!")
                QMessageBox.information(self, "Success", "✅ Connection successful!")
                conn.close()
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Error", f"❌ Connection failed:\n{err}")


# --- Run standalone ---
if __name__ == "__main__":
    app = QApplication([])
    window = SettingsPage()
    window.show()
    app.exec()
