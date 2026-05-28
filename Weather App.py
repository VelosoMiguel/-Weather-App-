import os
import sys
import requests
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# Load API key from environment variable — never hardcode secrets!
# Set it in your terminal: export OPENWEATHER_API_KEY="your_key_here"
API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")


class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weather App 🌤️")
        self.resize(400, 650)
        self.setStyleSheet("font-family: 'Segoe UI'; background-color: #F5F5F5;")

        self.is_celsius = True
        self.last_weather_data = None
        self.last_forecast_data = None

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(15)

        # Top bar
        top_layout = QHBoxLayout()
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Enter city name...")
        self.city_input.setFixedHeight(42)
        self.city_input.setStyleSheet("""
            QLineEdit {
                border-radius: 10px;
                border: 1px solid #616161;
                padding: 6px 10px;
                background: #E0E0E0;
                color: black;
                font-size: 15px;
            }
        """)
        self.city_input.returnPressed.connect(self.get_weather)

        self.search_button = QPushButton("Search")
        self.search_button.setFixedHeight(48)
        self.search_button.setFixedWidth(110)
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border-radius: 12px;
                font-weight: bold;
                font-size: 16px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #1565C0; }
        """)
        self.search_button.clicked.connect(self.get_weather)

        self.unit_button = QPushButton("°C")
        self.unit_button.setFixedWidth(60)
        self.unit_button.setFixedHeight(42)
        self.unit_button.setStyleSheet("""
            QPushButton {
                background-color: #42A5F5;
                color: white;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1E88E5; }
        """)
        self.unit_button.clicked.connect(self.toggle_unit)

        top_layout.addWidget(self.city_input)
        top_layout.addWidget(self.search_button)
        top_layout.addWidget(self.unit_button)
        self.layout.addLayout(top_layout)

        # Main labels
        self.temp_label = QLabel("--°C")
        self.temp_label.setAlignment(Qt.AlignCenter)
        self.temp_label.setFont(QFont("Segoe UI", 34, QFont.Bold))

        self.desc_label = QLabel("")
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setFont(QFont("Segoe UI", 16))

        self.extra_label = QLabel("")
        self.extra_label.setAlignment(Qt.AlignCenter)
        self.extra_label.setFont(QFont("Segoe UI", 12))

        self.emoji_label = QLabel("☀️")
        self.emoji_label.setAlignment(Qt.AlignCenter)
        self.emoji_label.setFixedSize(150, 150)
        self.emoji_label.setStyleSheet("QLabel { font-size: 100px; }")

        self.layout.addSpacing(20)
        self.layout.addWidget(self.temp_label)
        self.layout.addWidget(self.desc_label)
        self.layout.addWidget(self.extra_label)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.emoji_label, alignment=Qt.AlignCenter)
        self.layout.addSpacing(20)

        # Forecast section
        self.forecast_container = QFrame()
        self.forecast_layout = QVBoxLayout(self.forecast_container)
        self.forecast_container.setStyleSheet("""
            QFrame { background-color: white; border-radius: 15px; padding: 10px; }
        """)
        self.forecast_title = QLabel("5-Day Forecast")
        self.forecast_title.setAlignment(Qt.AlignCenter)
        self.forecast_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.forecast_layout.addWidget(self.forecast_title)
        self.layout.addWidget(self.forecast_container)

        # Auto-refresh every 10 minutes
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(10 * 60 * 1000)

        # Warn if API key is missing
        if not API_KEY:
            self.temp_label.setText("⚠️ No API key set")
            self.desc_label.setText("Set OPENWEATHER_API_KEY env variable")

    def get_weather(self):
        if not API_KEY:
            self.temp_label.setText("⚠️ No API key set")
            return

        city = self.city_input.text().strip()
        if not city:
            self.temp_label.setText("⚠️ Enter a city")
            return

        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
            data = requests.get(url, timeout=10).json()

            if data.get("cod") != 200:
                self.temp_label.setText("City not found")
                self.desc_label.clear()
                self.extra_label.clear()
                self.emoji_label.clear()
                self.forecast_title.clear()
                self._clear_forecast()
                self.last_weather_data = None
                self.last_forecast_data = None
                return

            self.last_weather_data = data
            self.display_weather(data)

            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
            forecast_data = requests.get(forecast_url, timeout=10).json()
            self.last_forecast_data = forecast_data
            self.display_forecast(forecast_data)

        except requests.exceptions.Timeout:
            self.temp_label.setText("Request timed out")
        except requests.exceptions.ConnectionError:
            self.temp_label.setText("No internet connection")
        except Exception as e:
            self.temp_label.setText("Unexpected error")
            print(f"Error: {e}")

    def display_weather(self, data):
        temp_c = data["main"]["temp"]
        desc = data["weather"][0]["description"].capitalize()
        wid = data["weather"][0]["id"]

        sunrise = datetime.fromtimestamp(data["sys"]["sunrise"])
        sunset = datetime.fromtimestamp(data["sys"]["sunset"])
        now = datetime.fromtimestamp(data["dt"])
        is_day = sunrise < now < sunset

        self.emoji_label.setText(self.get_weather_emoji(wid, is_day))

        if is_day:
            self.setStyleSheet("background-color: #E3F2FD; color: black; font-family: 'Segoe UI';")
            self.forecast_container.setStyleSheet("QFrame { background-color: white; border-radius: 15px; padding: 10px; }")
        else:
            self.setStyleSheet("background-color: #1E1E2F; color: white; font-family: 'Segoe UI';")
            self.forecast_container.setStyleSheet("QFrame { background-color: #2E2E3E; border-radius: 15px; padding: 10px; }")

        unit = "°C" if self.is_celsius else "°F"
        temp_display = f"{temp_c:.1f}°C" if self.is_celsius else f"{(temp_c * 9/5) + 32:.1f}°F"
        self.temp_label.setText(temp_display)
        self.desc_label.setText(desc)

        feels = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind = data.get("wind", {}).get("speed", 0)
        feels_disp = feels if self.is_celsius else (feels * 9/5) + 32
        self.extra_label.setText(
            f"Feels like: {feels_disp:.1f}{unit} | Humidity: {humidity}% | Wind: {wind} m/s"
        )

    def display_forecast(self, forecast_data):
        self._clear_forecast()

        if "list" not in forecast_data:
            return

        is_dark = "1E1E2F" in self.styleSheet()
        shown = set()
        for entry in forecast_data["list"]:
            date = entry["dt_txt"].split(" ")[0]
            if date not in shown:
                shown.add(date)
                temp = entry["main"]["temp"]
                if not self.is_celsius:
                    temp = (temp * 9/5) + 32
                unit = "°C" if self.is_celsius else "°F"
                emoji = self.get_weather_emoji(entry["weather"][0]["id"])
                day_label = QLabel(f"{date} • {temp:.1f}{unit} {emoji}")
                day_label.setAlignment(Qt.AlignCenter)
                day_label.setFont(QFont("Segoe UI", 13))
                day_label.setStyleSheet("color: white;" if is_dark else "color: black;")
                self.forecast_layout.addWidget(day_label)
                if len(shown) >= 5:
                    break

    def _clear_forecast(self):
        """Remove all forecast rows except the title."""
        for i in reversed(range(self.forecast_layout.count())):
            if i != 0:
                child = self.forecast_layout.itemAt(i)
                if child and child.widget():
                    child.widget().setParent(None)

    def toggle_unit(self):
        self.is_celsius = not self.is_celsius
        self.unit_button.setText("°C" if self.is_celsius else "°F")
        if self.last_weather_data:
            self.display_weather(self.last_weather_data)
        if self.last_forecast_data:
            self.display_forecast(self.last_forecast_data)

    def get_weather_emoji(self, wid, is_day=True):
        if 200 <= wid <= 232:
            return "⛈️"
        elif 300 <= wid <= 321:
            return "🌦️"
        elif 500 <= wid <= 531:
            return "🌧️"
        elif 600 <= wid <= 622:
            return "❄️"
        elif 701 <= wid <= 781:
            return "🌫️"
        elif wid == 800:
            return "☀️" if is_day else "🌙"
        elif 801 <= wid <= 804:
            return "🌤️" if is_day else "☁️"
        return "🌈"

    def auto_refresh(self):
        if self.city_input.text().strip():
            self.get_weather()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = WeatherApp()
    win.show()
    sys.exit(app.exec_())