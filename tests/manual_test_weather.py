import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.weather_utils import obtener_pronostico_meteo

print("--- Ejecución 1 ---")
print(obtener_pronostico_meteo())
