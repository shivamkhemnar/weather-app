"""Central configuration. All values have safe defaults so the app runs without .env."""
import os
from dotenv import load_dotenv

load_dotenv()  # safe if .env missing


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


# Seconds between autonomous data refresh cycles.
# Professional mode: 4 hours = 14400 sec (set REFRESH_HOURS=4).
# Demo mode: set SIMULATION_INTERVAL_SEC=10 for a fast classroom demo.
REFRESH_HOURS = _get_float("REFRESH_HOURS", 4.0)
SIMULATION_INTERVAL_SEC = _get_int("SIMULATION_INTERVAL_SEC", int(REFRESH_HOURS * 3600))

# Real API keys (optional - app falls back to simulation when missing).
# YOUR MANUAL WORK: get free keys and paste them into a `.env` file (see .env.example).
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "").strip()

# Optimization objective weights (cost, delay, risk, inventory)
COST_WEIGHT = _get_float("COST_WEIGHT", 0.35)
DELAY_WEIGHT = _get_float("DELAY_WEIGHT", 0.30)
RISK_WEIGHT = _get_float("RISK_WEIGHT", 0.25)
INVENTORY_WEIGHT = _get_float("INVENTORY_WEIGHT", 0.10)

# SQLite URL - relative to project root (C:\weather)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./supply_chain.db")

# All-India city coordinates (used by TomTom + OpenWeatherMap + map links)
CITY_COORDS = {
    "Mumbai": (19.0760, 72.8777),
    "Nashik": (19.9975, 73.7898),
    "Pune": (18.5204, 73.8567),
    "Delhi": (28.6139, 77.2090),
    "Jaipur": (26.9124, 75.7873),
    "Chennai": (13.0827, 80.2707),
    "Bangalore": (12.9716, 77.5946),
    "Hyderabad": (17.3850, 78.4867),
    "Kolkata": (22.5726, 88.3639),
    "Ahmedabad": (23.0225, 72.5714),
}
TRACKED_CITIES = ["Mumbai", "Nashik", "Pune", "Delhi", "Jaipur",
                  "Chennai", "Bangalore", "Hyderabad", "Kolkata", "Ahmedabad"]
