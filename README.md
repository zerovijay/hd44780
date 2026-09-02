# HD44780 MicroPython Driver

A simple MicroPython library for **HD44780** character LCD displays.  
Supports **direct GPIO** (4‑bit or 8‑bit) or **I2C** via a PCF8574 port expander.

---

## Features

- Connect using **GPIO** (4‑bit or 8‑bit) or **I2C** (PCF8574).
- Supports displays from 1–4 rows and 8–40 columns.
- Write text, move cursor, clear screen, turn display on/off.
- Show/hide cursor and enable/disable blinking.
- Scroll text left or right.
- Define and display up to 8 custom characters (5×8 pixel patterns).

---

## Installation

1. Copy `hd44780.py` to your project directory, or clone the repository:

   ```bash
   git clone https://github.com/zerovijay/hd44780.git
   ```

2. If you are using I2C, also copy `pcf8574.py` to your project directory, or clone the repository:

   ```bash
   git clone https://github.com/zerovijay/pcf8574.git
   ```

---

## Wiring

### Direct GPIO Mode

When creating the LCD object, you provide a list of pin numbers in this exact order:

- **8‑bit mode** (12 pins):  
  `[D0, D1, D2, D3, D4, D5, D6, D7, RS, RW, EN, BL]`

- **4‑bit mode** (8 pins):  
  `[D4, D5, D6, D7, RS, RW, EN, BL]`

> **Note:** `BL` is the backlight pin (optional, set to a dummy value if not used).

---

## Example Code

### 1. Direct GPIO (8‑bit)

```python
from hd44780 import HD44780_GPIO

# Pin assignment: D0..D7, RS, RW, EN, BL
lcd = HD44780_GPIO([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])

lcd.clear()
lcd.set_cursor(0, 0)
lcd.print("Hello, World!")
```

For **4‑bit** mode, add `nibble_mode=True`:

```python
lcd = HD44780_GPIO([0, 1, 2, 3, 4, 5, 6, 7], nibble_mode=True)
```

### 2. I2C Mode (with PCF8574)

```python
from machine import I2C, Pin
from hd44780 import HD44780_I2C
from pcf8574 import PCF8574

i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)
expander = PCF8574(i2c, 0x27)   # adjust address to match your module
lcd = HD44780_I2C(expander)

lcd.clear()
lcd.set_cursor(0, 0)
lcd.print("Hello, World!")
```

---

### 3. Adding a Custom Character

Create a custom character as a list of 8 numbers, each representing a row of a 5‑bit pattern.

Example: a heart symbol

```python
heart = [
    0b00000,
    0b01010,
    0b11111,
    0b11111,
    0b01110,
    0b00100,
    0b00000,
    0b00000,
]

lcd.add_custom_char(0, heart)   # store in slot 0
lcd.show_custom_char(0)         # display it
```

---

## API Reference

All methods work identically for both GPIO and I2C versions.

| Method                           | Description                                                               |
|--------------------------------- |-------------------------------------------------------------------------- |
| `print(text)`                    | Write text at the current cursor position.                                |
| `clear()`                        | Clear the entire screen and return cursor to home.                        |
| `home()`                         | Move cursor to row 0, column 0 (without clearing).                        |
| `set_cursor(row, col)`           | Move cursor to the specified position (row and col start at 0).           |
| `display(state)`                 | Turn the display on (`True`) or off (`False`).                            |
| `cursor(state)`                  | Show (`True`) or hide (`False`) the underline cursor.                     |
| `blink(state)`                   | Enable (`True`) or disable (`False`) cursor blinking.                     |
| `shift_display_left(steps=1)`    | Shift all displayed characters left by `steps`.                           |
| `shift_display_right(steps=1)`   | Shift all displayed characters right by `steps`.                          |
| `move_cursor_left(steps=1)`      | Move cursor left by `steps` positions.                                    |
| `move_cursor_right(steps=1)`     | Move cursor right by `steps` positions.                                   |
| `add_custom_char(slot, pattern)` | Store a custom character (slot 0–7) using an 8‑row bitmap (list of ints). |
| `show_custom_char(slot)`         | Display the custom character stored in `slot`.                            |
| `backlight(state)`               | Turn backlight on (`True`) or off (`False`) – **GPIO mode only**.         |

---

## Important Notes

- **I2C mode** – The backlight is always on (not yet controllable via software).  
  Only 4‑bit communication is supported.
- **GPIO mode** – Both 4‑bit and 8‑bit modes are supported, and backlight can be toggled.
- The driver uses fixed delays instead of polling the “busy” flag. This is sufficient for most applications and simplifies the code.

---

## License

This project is licensed under the [MIT License](LICENSE).
