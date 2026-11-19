"""Smooth fake maps covering all of India, for the planted-world tests. Light varies inside every state and is
only partly tied to buildings; NO2 rises towards the north (like the real Indo-Gangetic plain)."""
import numpy as np

def built(lat, lon, epoch=2020):
    b = 0.03 + 0.2 * (np.sin(lat * 6 + 1) * np.cos(lon * 5)) ** 2
    return b * {2015: 0.85, 2020: 1.0, 2025: 1.1}[epoch]

def radiance(lat, lon, year):
    extra = 4 * (np.sin(lat * 9) * np.cos(lon * 7 + 1)) ** 2       # lights not explained by buildings
    return (0.2 + 25 * built(lat, lon) + extra) * (1 + (0.02 + 0.06 * np.sin(lat + lon) ** 2) * (year - 2015))

def tree(lat, lon):
    return 0.2 + 0.4 * (np.cos(lat * 4) * np.sin(lon * 3 + 2)) ** 2

def crop(lat, lon):
    return 0.3 + 0.2 * np.sin(lat * 2) * np.cos(lon * 2)

def water(lat, lon):
    return 0.02 + 0.03 * np.cos(lat * 5) ** 2

def elevation(lat, lon):
    return 400 + 300 * np.sin(lat * 1.3) * np.cos(lon * 1.1)

def pop(lat, lon):
    return 40 * built(lat, lon) + 5 * np.sin(lat * 2 + lon) ** 2 + 1

def no2(lat, lon, year):
    return 1e-5 * (1 + 2 / (1 + np.exp(-(lat - 22) / 2.5)))
