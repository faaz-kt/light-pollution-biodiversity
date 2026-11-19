"""Smooth 'true' maps used by both the old files (lights/habitat CSVs) and the fake Earth Engine."""
import numpy as np

def built(lat, lon, epoch=2020):
    b = 0.02 + 0.35 * np.exp(-((lat - 12.97) ** 2 + (lon - 77.59) ** 2) / 0.4) + 0.05 * np.sin(3 * lat) ** 2 \
        + 0.25 * np.exp(-((lat - 10.0) ** 2 + (lon - 76.3) ** 2) / 0.3)
    return np.clip(b * {2015: 0.8, 2020: 1.0, 2025: 1.15}[epoch], 0, 1)

def tree(lat, lon):
    return np.clip(0.15 + 0.55 * np.exp(-((lon - 75.2) ** 2) / 0.4) + 0.05 * np.cos(lat * 4), 0, 1)

def crop(lat, lon):
    return np.clip(0.3 + 0.2 * np.sin(lat * 2) * np.cos(lon * 2), 0, 1)

def water(lat, lon):
    return 0.02 + 0.03 * np.cos(lat * 5) ** 2

def elevation(lat, lon):
    return 600 + 300 * np.sin(lat) * np.cos(lon)

def radiance(lat, lon, year):
    g = 0.02 + 0.12 * np.sin(lat * 3 + lon) ** 2
    return (0.3 + 30 * built(lat, lon)) * (1 + g * (year - 2015)) * (1 + 0.1 * np.sin(lat * 7 + lon * 3))

def pop(lat, lon):
    return 50 * built(lat, lon) + 2

def no2(lat, lon, year):
    return 1e-5 * (1 + built(lat, lon)) * (1 + 0.01 * (year - 2019))
