"""
BMP280 sensor reader package.

This package provides tools for reading data from BMP280 temperature
and pressure sensors via I2C.
"""

from .bmp280_reader import BMP280Reader

__all__ = ['BMP280Reader']
__version__ = '0.1.0'
