import os
import json
import mysql.connector
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLineEdit, QPushButton,
    QVBoxLayout, QFormLayout, QMessageBox, QStackedWidget, QLabel, QHBoxLayout
)
from Databases.MySQL.connection import DatabaseManager


# -----------------------------
# Common Paths
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "..", "SavedData")
os.makedirs(SAVE_DIR, exist_ok=True)

DB_SETTINGS_FILE = os.path.join(SAVE_DIR, "db_settings.json")
LLM_SETTINGS_FILE = os.path.join(SAVE_DIR, "llm_settings.json")


# -----------------------------
# 🧩 Page 1: Database Settings
# -----------------------------
class DatabaseSettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚙️ Database Settings")
        self.setFixedSize(400, 270)
        self.setStyleSheet(self._style())

        # Inputs
        self.host_input = QLineEdit()
        self.port_input = QLineEdit("3306")
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.db_input = QLineEdit()

        # Load saved data
        self.load_settings()

        # Buttons
        self.test_btn = QPushButton("🔍 Test Connection")
        self.save_btn = QPushButton("💾 Save Settings")

        self.test_btn.clicked.connect(self.test_connection)
        self.save_btn.clicked.connect(self.save_settings)

        # Layout
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

    def _style(self):
        return """
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
            QPushButton:hover { background-color: #666; }
        """

    def load_settings(self):
        if os.path.exists(DB_SETTINGS_FILE):
            with open(DB_SETTINGS_FILE, "r") as f:
                data = json.load(f)
                self.host_input.setText(data.get("host", ""))
                self.port_input.setText(data.get("port", "3306"))
                self.user_input.setText(data.get("user", ""))
                self.pass_input.setText(data.get("password", ""))
                self.db_input.setText(data.get("database", ""))

    def save_settings(self):
        data = {
            "host": self.host_input.text(),
            "port": self.port_input.text(),
            "user": self.user_input.text(),
            "password": self.pass_input.text(),
            "database": self.db_input.text(),
        }
        with open(DB_SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=4)
        QMessageBox.information(self, "Saved", "✅ Database settings saved!")

    def test_connection(self):
        try:
            conn = DatabaseManager(
                host=self.host_input.text(),
                port=int(self.port_input.text()),
                user=self.user_input.text(),
                password=self.pass_input.text(),
                database=self.db_input.text(),
            )
            if conn:
                QMessageBox.information(self, "Success", "✅ Connection successful!")
                conn.close()
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Error", f"❌ Connection failed:\n{err}")


# -----------------------------
# 🤖 Page 2: LLM Settings
# -----------------------------
class LLMSettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧠 LLM Settings")
        self.setFixedSize(400, 300)
        self.setStyleSheet(DatabaseSettingsPage()._style())

        # Inputs
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.model_input = QLineEdit("gpt-4o-mini")
        self.temp_input = QLineEdit("0.2")

        # Load settings if exists
        self.load_settings()

        # Buttons
        self.save_btn = QPushButton("💾 Save LLM Settings")

        self.save_btn.clicked.connect(self.save_settings)

        # Layout
        form = QFormLayout()
        form.addRow("API Key:", self.api_key_input)
        form.addRow("Model:", self.model_input)
        form.addRow("Temperature:", self.temp_input)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.save_btn)
        self.setLayout(layout)

    def load_settings(self):
        if os.path.exists(LLM_SETTINGS_FILE):
            with open(LLM_SETTINGS_FILE, "r") as f:
                data = json.load(f)
                self.api_key_input.setText(data.get("api_key", ""))
                self.model_input.setText(data.get("model", "gpt-4o-mini"))
                self.temp_input.setText(str(data.get("temperature", "0.2")))

    def save_settings(self):
        data = {
            "api_key": self.api_key_input.text(),
            "model": self.model_input.text(),
            "temperature": float(self.temp_input.text()),
        }
        with open(LLM_SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=4)
        QMessageBox.information(self, "Saved", "✅ LLM settings saved!")


# -----------------------------
# 🪟 Main Window with Navigation
# -----------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚙️ QueryCrafter Settings")
        self.setFixedSize(520, 400)
        self.setStyleSheet(DatabaseSettingsPage()._style())

        # Pages
        self.pages = QStackedWidget()
        self.db_page = DatabaseSettingsPage()
        self.llm_page = LLMSettingsPage()
        self.pages.addWidget(self.db_page)
        self.pages.addWidget(self.llm_page)

        # Navigation Buttons
        self.next_btn = QPushButton("➡️ Next (LLM Settings)")
        self.back_btn = QPushButton("⬅️ Back to Database")
        self.back_btn.hide()

        self.next_btn.clicked.connect(self.goto_llm)
        self.back_btn.clicked.connect(self.goto_db)

        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.next_btn)

        layout = QVBoxLayout()
        layout.addWidget(self.pages)
        layout.addLayout(nav_layout)
        self.setLayout(layout)

    def goto_llm(self):
        self.pages.setCurrentIndex(1)
        self.next_btn.hide()
        self.back_btn.show()

    def goto_db(self):
        self.pages.setCurrentIndex(0)
        self.back_btn.hide()
        self.next_btn.show()


# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
