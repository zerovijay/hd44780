"""
MicroPython driver for HD44780-compatible LCD displays.

Supports I2C (PCF8574) and direct GPIO interfaces with 4-bit and 8-bit
parallel modes. Provides full control over display operations including
custom characters, cursor management, and backlight control.
"""

from .src.hd44780 import HD44780_GPIO, HD44780_I2C

__version__ = "1.0.0"
__author__ = "Vijay"
__email__ = "vijay98.dev@gmail.com"
__license__ = "MIT"
__description__ = (
    "MicroPython driver for HD44780-compatible LCD displays with I2C and GPIO support"
)
__url__ = "https://github.com/zerovijay/hd44780"

__all__ = ["HD44780_I2C", "HD44780_GPIO"]
