import utime
from machine import Pin

from micropython import const
from pcf8574 import PCF8574


class HD44780:
    """
    HD44780 LCD controller base driver.

    Defines the command set and common operations for HD44780-compatible
    LCD displays. Subclass this to implement hardware-specific communication.
    """

    # Clear display
    CMD_CLEAR_DISPLAY: int = const(0x01)

    # Return home
    CMD_RETURN_HOME: int = const(0x02)

    # Entry mode set
    CMD_ENTRY_MODE_SET: int = const(0x04)
    CMD_INCREMENT: int = const(0x02)
    CMD_SHIFT: int = const(0x01)

    # Display control
    CMD_DISPLAY_CTRL: int = const(0x08)
    CMD_DISPLAY_ON: int = const(0x04)
    CMD_CURSOR_ON: int = const(0x02)
    CMD_BLINK_ON: int = const(0x01)

    # Cursor or display shift
    CMD_CURSOR_DISPLAY_SHIFT: int = const(0x10)
    CMD_DISPLAY_SHIFT: int = const(0x08)
    CMD_CURSOR_MOVE: int = const(0x00)
    CMD_SHIFT_LEFT: int = const(0x00)
    CMD_SHIFT_RIGHT: int = const(0x04)

    # Function set
    CMD_FUNCTION_SET: int = const(0x20)
    CMD_8_BIT_MODE: int = const(0x10)
    CMD_4_BIT_MODE: int = const(0x00)
    CMD_2_LINE: int = const(0x08)
    CMD_1_LINE: int = const(0x00)
    CMD_5X10_DOTS: int = const(0x04)
    CMD_5X8_DOTS: int = const(0x00)

    # Set CGRAM address
    CMD_SET_CGRAM_ADDR: int = const(0x40)

    # Set DDRAM address
    CMD_SET_DDRAM_ADDR: int = const(0x80)

    # DDRAM base addresses for 4 rows
    ROW_OFFSETS: tuple[int, ...] = const(
        (
            0x00,  # Row 0: 0x00
            0x40,  # Row 1: 0x40
            0x14,  # Row 2: 0x14 (for 20+ column displays)
            0x54,  # Row 3: 0x54 (for 20+ column displays)
        )
    )

    def __init__(
        self, rows: int, columns: int, font5x10: bool, nibble_mode: bool
    ) -> None:
        """
        Initialize the HD44780 instance.

        :param rows: Number of display rows (1-4).
        :param columns: Number of display columns (8-40 typically).
        :param font5x10: True for 5x10 dot font, False for 5x8 dot font.
        :param nibble_mode: True for 4-bit mode, False for 8-bit mode.
        :raises ValueError: If rows or columns are invalid.
        """
        if not 1 <= rows <= 4:
            raise ValueError("rows must be between 1 and 4")

        if not 8 <= columns <= 40:
            raise ValueError("columns must be between 8 and 40")

        self._rows: int = rows
        self._columns: int = columns
        self._font5x10: bool = font5x10
        self._nibble_mode: bool = nibble_mode

    def _hd44780_read(self, rs: bool = True) -> int:
        """
        Read data or busy flag from the HD44780.

        Defines the communication interface for reading from the HD44780.
        Subclasses implement the actual data reception according to their
        specific hardware interface and bus width.

        :param rs: Register Select flag. False for busy flag, True for data.
        :return: The byte read from the HD44780 (0-255).
        :raises NotImplementedError: Must be implemented by subclass.
        """
        raise NotImplementedError

    def _hd44780_write(self, data: int, rs: bool = False) -> None:
        """
        Write a command or data byte to the HD44780.

        Defines the communication interface for writing to the HD44780.
        Subclasses implement the actual data transmission according to
        their specific hardware interface and bus width.

        :param data: Byte value to send (0-255).
        :param rs: Register Select flag. False for command, True for data.
        :raises NotImplementedError: Must be implemented by subclass.
        """
        raise NotImplementedError

    def backlight(self, state: bool) -> None:
        """
        Control the backlight state.

        Defines the communication interface for backlight control.
        Subclasses implement the actual backlight control according to
        their specific hardware interface.

        :param state: True to turn on, False to turn off.
        :raises NotImplementedError: Must be implemented by subclass.
        """
        raise NotImplementedError

    def _hd44780_init(self) -> None:
        """
        Initialize the LCD display.

        Performs the power-on initialization sequence as specified in the
        HD44780 datasheets for both 4-bit and 8-bit modes.
        """
        # Wait for more than 40 ms after VCC rises to 2.7V.
        utime.sleep_ms(50)

        # Function set: Interface is 8 bits long.
        self._hd44780_write(self.CMD_FUNCTION_SET | self.CMD_8_BIT_MODE)

        # Wait for more than 4.1ms.
        utime.sleep_ms(5)

        # Function set: Interface is 8 bits long.
        self._hd44780_write(self.CMD_FUNCTION_SET | self.CMD_8_BIT_MODE)

        # Wait for more than 100us.
        utime.sleep_us(100)

        # Function set: Interface is 8 bits long.
        self._hd44780_write(self.CMD_FUNCTION_SET | self.CMD_8_BIT_MODE)

        # Function set: Interface is 4 bits long.
        if self._nibble_mode:
            self._hd44780_write(self.CMD_FUNCTION_SET >> 4)

        # Function set: Specify the interface length, number of display lines,
        # and character font. The number of display lines and character font
        # cannot be changed after this point.
        self._hd44780_write(
            self.CMD_FUNCTION_SET
            | (self.CMD_4_BIT_MODE if self._nibble_mode else self.CMD_8_BIT_MODE)
            | (self.CMD_2_LINE if self._rows >= 2 else self.CMD_1_LINE)
            | (self.CMD_5X10_DOTS if self._font5x10 else self.CMD_5X8_DOTS)
        )

        # Display control: Turn display on with cursor and blink off
        self._hd44780_write(self.CMD_DISPLAY_CTRL | self.CMD_DISPLAY_ON)

        # Clear display
        self._hd44780_write(self.CMD_CLEAR_DISPLAY)
        utime.sleep_ms(2)

        # Set entry mode: increment cursor position, no shift
        self._hd44780_write(self.CMD_ENTRY_MODE_SET | self.CMD_INCREMENT)

    def clear(self) -> None:
        """
        Clear the entire display and set DDRAM address 0 in the address counter.
        """
        self._hd44780_write(self.CMD_CLEAR_DISPLAY)
        utime.sleep_ms(2)

    def home(self) -> None:
        """
        Set DDRAM address 0 in the address counter.

        Also returns the display from being shifted to its original position.
        DDRAM contents remain unchanged.
        """
        self._hd44780_write(self.CMD_RETURN_HOME)
        utime.sleep_ms(2)

    def display(self, state: bool) -> None:
        """
        Turn the display on or off.

        :param state: True to turn on, False to turn off.
        """
        ctrl: int = self.CMD_DISPLAY_CTRL
        if state:
            ctrl |= self.CMD_DISPLAY_ON
        self._hd44780_write(ctrl)

    def cursor(self, state: bool) -> None:
        """
        Show or hide the cursor.

        :param state: True to show, False to hide.
        """
        ctrl: int = self.CMD_DISPLAY_CTRL | self.CMD_DISPLAY_ON
        if state:
            ctrl |= self.CMD_CURSOR_ON
        self._hd44780_write(ctrl)

    def blink(self, state: bool) -> None:
        """
        Enable or disable cursor blinking.

        :param state: True to enable blinking, False to disable.
        """
        ctrl: int = self.CMD_DISPLAY_CTRL | self.CMD_DISPLAY_ON | self.CMD_CURSOR_ON
        if state:
            ctrl |= self.CMD_BLINK_ON
        self._hd44780_write(ctrl)

    def shift_display_left(self, steps: int = 1) -> None:
        """
        Shift the entire display left by the specified number of steps.

        :param steps: Number of positions to shift. Defaults to 1.
        """
        cmd: int = (
            self.CMD_CURSOR_DISPLAY_SHIFT | self.CMD_DISPLAY_SHIFT | self.CMD_SHIFT_LEFT
        )
        for _ in range(steps):
            self._hd44780_write(cmd)
            utime.sleep_us(50)

    def shift_display_right(self, steps: int = 1) -> None:
        """
        Shift the entire display right by the specified number of steps.

        :param steps: Number of positions to shift. Defaults to 1.
        """
        cmd: int = (
            self.CMD_CURSOR_DISPLAY_SHIFT
            | self.CMD_DISPLAY_SHIFT
            | self.CMD_SHIFT_RIGHT
        )
        for _ in range(steps):
            self._hd44780_write(cmd)
            utime.sleep_us(50)

    def move_cursor_left(self, steps: int = 1) -> None:
        """
        Move the cursor left by the specified number of steps.

        :param steps: Number of positions to move. Defaults to 1.
        """
        cmd: int = (
            self.CMD_CURSOR_DISPLAY_SHIFT | self.CMD_CURSOR_MOVE | self.CMD_SHIFT_LEFT
        )
        for _ in range(steps):
            self._hd44780_write(cmd)
            utime.sleep_us(50)

    def move_cursor_right(self, steps: int = 1) -> None:
        """
        Move the cursor right by the specified number of steps.

        :param steps: Number of positions to move. Defaults to 1.
        """
        cmd: int = (
            self.CMD_CURSOR_DISPLAY_SHIFT | self.CMD_CURSOR_MOVE | self.CMD_SHIFT_RIGHT
        )
        for _ in range(steps):
            self._hd44780_write(cmd)
            utime.sleep_us(50)

    def set_cursor(self, row: int, column: int) -> None:
        """
        Set the cursor to the specified row and column.

        :param row: Row number (0-indexed).
        :param column: Column number (0-indexed).
        :raises ValueError: If row or column is out of range.
        """
        if not 0 <= row <= self._rows:
            raise ValueError(f"row must be between 0 and {self._rows - 1}")

        if not 0 <= column <= self._columns:
            raise ValueError(f"column must be between 0 and {self._columns - 1}")

        self._hd44780_write(self.CMD_SET_DDRAM_ADDR | (self.ROW_OFFSETS[row] + column))

    def print(self, text: str) -> None:
        """
        Print a string of text to the LCD at the current cursor position.

        :param text: String to display on the LCD.
        """
        for char in text:
            self._hd44780_write(ord(char), True)  # True = data mode

    def add_custom_char(self, slot: int, bitmap: list[int]) -> None:
        """
        Add a custom character to CGRAM.

        Each custom character uses 8 bytes of CGRAM.
        The bitmap should be a list of 8 bytes, each representing one row.
        Only the lower 5 bits of each byte are used (bits 4-0).

        :param slot: CGRAM slot (0-7).
        :param bitmap: List of 8 bytes (0-31) representing the character pattern.
        :raises ValueError: If slot is out of range or bitmap is invalid.
        """
        if not 0 <= slot <= 7:
            raise ValueError("slot must be between 0 and 7")

        if len(bitmap) != 8:
            raise ValueError("bitmap must contain exactly 8 rows")

        if any(not 0 <= row <= 0x1F for row in bitmap):
            raise ValueError("bitmap rows must contain values between 0 and 31")

        # Set CGRAM address (each character uses 8 bytes)
        self._hd44780_write(self.CMD_SET_CGRAM_ADDR | (slot << 3))

        # Write the character bitmap
        for row in bitmap:
            self._hd44780_write(row, True)  # Data mode
            utime.sleep_us(50)

        # Return to DDRAM (display memory)
        self._hd44780_write(self.CMD_SET_DDRAM_ADDR)

    def show_custom_char(self, slot: int) -> None:
        """
        Display a custom character at the current cursor position.

        :param slot: CGRAM slot (0-7).
        :raises ValueError: If slot is out of range.
        """
        if not 0 <= slot <= 7:
            raise ValueError("slot must be between 0 and 7")

        self._hd44780_write(slot, True)  # Data mode, value 0-7 for custom chars


class HD44780_I2C(HD44780):
    """
    HD44780 LCD driver with I2C interface using PCF8574.

    Implements 4-bit communication over I2C through a PCF8574 GPIO expander.

    Pin mapping:
        Bit 7: DB7 (Data bit 7)
        Bit 6: DB6 (Data bit 6)
        Bit 5: DB5 (Data bit 5)
        Bit 4: DB4 (Data bit 4)
        Bit 3: BL  (Backlight)
        Bit 2: EN  (Enable)
        Bit 1: RW  (Read/Write)
        Bit 0: RS  (Register Select)
    """

    RS: int = const(0x01)  # Register Select
    RW: int = const(0x02)  # Read/Write
    EN: int = const(0x04)  # Enable
    BL: int = const(0x08)  # Backlight

    def __init__(
        self, gpio: PCF8574, rows: int = 2, columns: int = 16, font5x10: bool = False
    ) -> None:
        """
        Initialize the I2C-based HD44780 LCD display.

        :param gpio: PCF8574 GPIO expander object.
        :param rows: Number of display rows. Defaults to 2.
        :param columns: Number of display columns. Defaults to 16.
        :param font5x10: True for 5x10 dot font, False for 5x8 dot font. Defaults to False.
        :raises RuntimeError: If gpio is not a valid PCF8574 object.
        """
        super().__init__(rows, columns, font5x10, True)

        if not isinstance(gpio, PCF8574):
            raise RuntimeError("Invalid PCF8574 GPIO expander object")

        # PCF8574 object
        self._gpio: PCF8574 = gpio
        self._gpio.gpio_set_mode_masked(0xFF, PCF8574.GPIO_MODE_OUTPUT)

        # Initialize LCD in 4-bit mode
        self._hd44780_init()

    def _write_nibble(self, nibble: int, rs: bool) -> None:
        """
        Send a single nibble (4 bits) with an enable pulse.

        The nibble is placed on the upper 4 bits of the PCF8574 port
        (bits 4-7), while the control signals (RS, EN) are set as specified.
        The backlight bit (BL) is always enabled during writes.

        :param nibble: 4-bit value to send (0-15). Only the lower 4 bits are used.
        :param rs: Register Select flag. False for command, True for data.
        """
        # Construct the complete payload for the PCF8574
        payload: int = (self.RS if rs else 0x00) | self.BL | (nibble << 4)

        self._gpio.gpio_port_write(payload)
        utime.sleep_us(1)
        self._gpio.gpio_port_write(payload | self.EN)
        utime.sleep_us(1)
        self._gpio.gpio_port_write(payload & ~self.EN)
        utime.sleep_us(50)

    def _hd44780_write(self, data: int, rs: bool = False) -> None:
        """
        Write a command or data byte via I2C.

        Implements the 4-bit protocol:
        1. Send the high nibble with an enable pulse.
        2. Send the low nibble with an enable pulse.

        :param data: Byte value to send.
        :param rs: Register Select flag. False for command, True for data.
        """
        # Send high nibble (bits 7-4)
        self._write_nibble((data >> 4) & 0x0F, rs)

        # Send low nibble (bits 3-0)
        self._write_nibble(data & 0x0F, rs)

    def backlight(self, state: bool) -> None:
        """
        Control the backlight state via I2C.

        This method is not yet implemented. When implemented, it will toggle
        PCF8574 bit 3 (BL) while preserving the state of all other pins
        (RS, RW, EN, data pins).

        :param state: True to turn on, False to turn off.
        :raises NotImplementedError: Backlight control is not yet implemented.
        """
        # TODO: Implement backlight control
        # Need to read current port state, modify BL bit, then write back
        raise NotImplementedError


class HD44780_GPIO(HD44780):
    """
    HD44780 LCD driver with direct GPIO interface.

    Supports both 4-bit and 8-bit parallel communication modes.
    Pin mapping (ordered from LSB to MSB + control pins):
        8-bit: [D0, D1, D2, D3, D4, D5, D6, D7, RS, RW, EN, BL]
        4-bit: [D4, D5, D6, D7, RS, RW, EN, BL]
    """

    def __init__(
        self,
        pins: list[int],
        rows: int = 2,
        columns: int = 16,
        font5x10: bool = False,
        nibble_mode: bool = False,
    ) -> None:
        """
        Initialize the GPIO-based HD44780 LCD display.

        :param pins: List of pin numbers.
            - 8-bit: [D0-D7, RS, RW, EN, BL] (12 pins)
            - 4-bit: [D4-D7, RS, RW, EN, BL] (8 pins)
        :param rows: Number of display rows. Defaults to 2.
        :param columns: Number of display columns. Defaults to 16.
        :param font5x10: True for 5x10 dot font. Defaults to False.
        :param nibble_mode: True for 4-bit mode, False for 8-bit mode. Defaults to False.
        :raises ValueError: If the pin list length is invalid.
        """
        # Validate pin count
        expected_pin_count: int = 8 if nibble_mode else 12
        if len(pins) != expected_pin_count:
            raise ValueError(
                f"{'4-bit' if nibble_mode else '8-bit'} mode requires "
                f"{expected_pin_count} pins, got {len(pins)}"
            )

        super().__init__(rows, columns, font5x10, nibble_mode)

        # Create all GPIO pins
        self._pins: list[Pin] = [Pin(pin, Pin.OUT) for pin in pins]

        # Extract data pins (first 4 or 8 pins)
        self._data_count: int = 4 if nibble_mode else 8
        self._data_pins: list[Pin] = self._pins[: self._data_count]

        # Extract control pins (last 4 pins: RS, RW, EN, BL)
        self._rs_pin: Pin = self._pins[-4]  # Register Select
        self._rw_pin: Pin = self._pins[-3]  # Read/Write
        self._en_pin: Pin = self._pins[-2]  # Enable
        self._bl_pin: Pin = self._pins[-1]  # Backlight

        # Set initial states
        self._en_pin.value(0)  # Enable low
        self._rw_pin.value(0)  # Write mode
        self._bl_pin.value(1)  # Backlight on

        # Initialize LCD
        self._hd44780_init()

    def _pulse_enable(self) -> None:
        """
        Generate an enable pulse to latch the data.
        """
        self._en_pin.value(1)
        utime.sleep_us(1)  # Enable pulse width min 450ns
        self._en_pin.value(0)
        utime.sleep_us(1)  # Enable cycle time min 500ns

    def _write_nibble(self, nibble: int) -> None:
        """
        Write a 4-bit nibble to the data pins and pulse enable.

        :param nibble: 4-bit value to send (0-15).
        """
        # Set data pins (D4-D7 in 4-bit mode)
        for i in range(4):
            self._data_pins[i].value((nibble >> i) & 1)

        # Pulse enable to latch data
        self._pulse_enable()

    def _write_byte(self, byte: int) -> None:
        """
        Write an 8-bit byte to the data pins and pulse enable.

        :param byte: 8-bit value to send (0-255).
        """
        # Set all data pins (D0-D7 in 8-bit mode)
        for i in range(8):
            self._data_pins[i].value((byte >> i) & 1)

        # Pulse enable to latch data
        self._pulse_enable()

    def _hd44780_write(self, data: int, rs: bool = False) -> None:
        """
        Write a command or data byte to the HD44780.

        :param data: Byte value to send (0-255).
        :param rs: Register Select flag. False for command, True for data.
        """
        # Set control signals
        self._rs_pin.value(rs)
        self._rw_pin.value(False)  # Write mode

        if self._nibble_mode:
            # 4-bit mode: Send high nibble then low nibble
            self._write_nibble((data >> 4) & 0x0F)  # High nibble
            self._write_nibble(data & 0x0F)  # Low nibble
        else:
            # 8-bit mode: Send all bits at once
            self._write_byte(data)

        utime.sleep_us(50)  # Delay for LCD to process

    def backlight(self, state: bool) -> None:
        """
        Turn the backlight on or off.

        :param state: True to turn on, False to turn off.
        """
        self._bl_pin.value(state)
