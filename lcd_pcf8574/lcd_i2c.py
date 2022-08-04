# SPDX-FileCopyrightText: Copyright (c) 2022 Evin Dunn
# SPDX-License-Identifier: MIT

"""
LCD class for interfacing with PCF8574-based I2C character LCDs
"""

from time import sleep
from struct import pack, unpack

from busio import I2C
from adafruit_bus_device.i2c_device import I2CDevice


DEFAULT_COLUMNS = 16
DEFAULT_ROWS = 2
DEFAULT_ADDR = 0x27

MILLISECOND = 1e-3
MICROSECOND = 1e-6

# Instruction set
FUNCTIONSET = 0x20
MODE_4BIT = 0x00
MODE_2LINE = 0x08
MODE_5X8DOT = 0x00

RETURN_HOME = 0x02
DISPLAY_CLEAR = 0x01

DISPLAY_SET = 0x08
DISPLAY_ON = 0x04
DISPLAY_OFF = 0x00
CURSOR_ON = 0x02
CURSOR_OFF = 0x00
BLINK_ON = 0x01
BLINK_OFF = 0x00

ENTRY_MODE_SET = 0x04
CURSOR_INCREMENT = 0x02
CURSOR_DECREMENT = 0x00

CURSOR_SET = 0x10
CURSOR_RIGHT = 0x04
CURSOR_LEFT = 0x00
DISPLAY_SHIFT = 0x01
CURSOR_MOVE = 0x00

FLAG_BACKLIGHT_ON = 0x08
FLAG_BACKLIGHT_OFF = 0x00
FLAG_DATA_ENABLE = 0x04
FLAG_READ_ENABLE = 0x02
FLAG_WRITE_ENABLE = 0x00
FLAG_REGISTER_DATA = 0x01
FLAG_REGISTER_INSTRUCTION = 0x00
FLAG_LCD_BUSY = 0b10000000

CURSOR_POS_SET = 0b10000000

ADDR_COL_INCREMENT = 0x01
ADDR_ROW_INCREMENT = 0x40


class LCD:
    """
    PCF8574-based I2C interface to a HD44780-based character LCD. The chips
    are tied together with the following configuration:

    PCF8574 SDA: P7 P6 P5 P4 P3        P2 P1  P0
    HD44780 LCD: D7 D6 D5 D4 Backlight E  RWB RS


    Datasheets:
        - https://www.ti.com/lit/ds/symlink/pcf8574.pdf
        - https://www.sparkfun.com/datasheets/LCD/HD44780.pdf
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self, sda, scl, address=DEFAULT_ADDR, rows=DEFAULT_ROWS, columns=DEFAULT_COLUMNS
    ):

        # Max frequency for the PCF8574 is 100 kHz
        i2c = I2C(sda=sda, scl=scl, frequency=100000)

        self.i2c = I2CDevice(i2c, address)
        self._backlight = FLAG_BACKLIGHT_OFF
        self._write_enable = FLAG_WRITE_ENABLE
        self._register = FLAG_REGISTER_INSTRUCTION

        self._cursor = CURSOR_ON
        self._blink = BLINK_OFF
        self._display_state = DISPLAY_ON

        self._rows = rows
        self._columns = columns
        self._current_row = 0
        self._current_column = 0

        # Wait for power-on
        sleep(20 * MILLISECOND)

        mode_4bit = FUNCTIONSET | MODE_4BIT
        modeset_high = pack(">B", mode_4bit | FLAG_DATA_ENABLE)
        modeset_low = pack(">B", mode_4bit & ~FLAG_DATA_ENABLE)
        with self.i2c:
            self.i2c.write(modeset_low)
            sleep(MILLISECOND)
            self.i2c.write(modeset_high)
            sleep(MILLISECOND)
            self.i2c.write(modeset_low)
            sleep(MILLISECOND)

        self._send(mode_4bit | MODE_2LINE | MODE_5X8DOT)
        self.clear()

        self._configure_display()
        self._send(ENTRY_MODE_SET | CURSOR_INCREMENT)

        self.backlight(True)

    def clear(self):
        """
        Clears the display and returns the cursor to the origin
        """
        self._write_enable = FLAG_WRITE_ENABLE
        self._register = FLAG_REGISTER_INSTRUCTION
        self._send(DISPLAY_CLEAR)

    def backlight(self, backlight: bool):
        """
        :param backlight: Whether the backlight should be enabled
        """
        self._backlight = FLAG_BACKLIGHT_ON if backlight else FLAG_BACKLIGHT_OFF
        self._write_enable = FLAG_WRITE_ENABLE
        self._register = FLAG_REGISTER_INSTRUCTION
        self._send_byte(0)

    def cursor(self, cursor: bool):
        """
        :param cursor: Whether the cursor should be enabled
        """
        self._cursor = CURSOR_ON if cursor else CURSOR_OFF
        self._configure_display()

    def blink(self, blink: bool):
        """
        :param blink: Whether cursor blink should be enabled
        """
        self._blink = BLINK_ON if blink else BLINK_OFF
        self._configure_display()

    def home(self):
        """
        Returns the cursor to the origin without clearing the display
        """
        self._write_enable = FLAG_WRITE_ENABLE
        self._register = FLAG_REGISTER_INSTRUCTION
        self._current_row = 0
        self._current_column = 0
        self._send(RETURN_HOME)

    def set_position(self, row: int, col: int):
        """
        Sets the cursor position
        :param row: zero-indexed cursor row
        :param col: zero-index cursor column
        """
        prev_write_enable = self._write_enable
        prev_register = self._register

        self._write_enable = FLAG_WRITE_ENABLE
        self._register = FLAG_REGISTER_INSTRUCTION
        self._current_row = row % self._rows
        self._current_column = col % self._columns
        cursor_addr = (
            self._current_row * ADDR_ROW_INCREMENT
            + self._current_column * ADDR_COL_INCREMENT
        )
        self._send(CURSOR_POS_SET | cursor_addr)

        self._write_enable = prev_write_enable
        self._register = prev_register

    def write(self, value: str):
        """
        Writes a string to the LCD at the current cursor position
        :param value: The string to write to the LCD
        """
        self._write_enable = FLAG_WRITE_ENABLE
        self._register = FLAG_REGISTER_DATA
        for char in value:
            if char == "\n" or self._current_column == self._columns:
                row = (self._current_row + 1) % self._rows
                col = 0
                self.set_position(row, col)

            self._send(ord(char))
            self._current_column += 1

    @property
    def _lsb(self):
        """
        Bits 3, 1, and 0 of every I2C request based on the current values
        of:
            - Whether the backlight should be turned on
            - Whether we're reading from or writing to the HD44780 LCD
            - Whether we're using the instruction or data register of the LCD

        PCF8574 SDA: D3        D1  D0
        HD44780 LCD: Backlight RWB RS
        """
        return self._backlight | self._write_enable | self._register

    def _configure_display(self):
        """
        Configures the display on/off state, cursor on/off state, and blink
        on/off state of the LCD
        """
        self._write_enable = FLAG_WRITE_ENABLE
        self._register = FLAG_REGISTER_INSTRUCTION
        self._send(DISPLAY_SET | self._display_state | self._cursor | self._blink)

    def _wait_for_ready(self):
        """
        Poll the LCD until the ready flag is not set and the LCD is ready to
        accept a new packet
        """
        prev_write_enable = self._write_enable
        prev_register = self._register

        self._write_enable = FLAG_READ_ENABLE
        self._register = FLAG_REGISTER_INSTRUCTION

        is_busy = True
        while is_busy:
            response_byte = self._send_byte(0)
            is_busy = response_byte & FLAG_LCD_BUSY > 0

        self._write_enable = prev_write_enable
        self._register = prev_register

    def _send(self, byte: int):
        """
        Wait for the LCD to be ready, then send the given byte
        :param byte: The 0-255 int to send to the LCD
        """
        self._wait_for_ready()
        self._send_byte(byte)

    def _send_byte(self, byte: int):
        """
        Sends the given byte to the LCD in two 4-bit packets

        D7-D4 are 4 bits of the instruction that we're sending to the LCD
        D3-D0 are the backlight, LCD enable (E), read/write (RWB), and register
        select (RS) pins, respectively

        It takes two of these packets to send the full byte, big-endian order

        Each packet consists of 4 I2C requests:
            - Write the packet with the enable bit (E) low
            - Write the packet with the enable bit (E) high
            - Read the response off of the bus while enable (E) is high
            - Write the packet with the enable bit low

        The 1-byte response, if applicable, is read as two 1-byte I2C messages,
        big-endian order, where D7-D4 contain the data bits and bits D3-D0 are
        ignored (since backlight enable, E, RWB, RS are write-only values).

        :param byte: The 0-255 int to send to the LCD
        """
        val_nib_high = byte & 0b11110000
        val_nib_low = (byte & 0b00001111) << 4

        response_buf = bytearray(2)

        with self.i2c:
            for idx, nib in enumerate([val_nib_high, val_nib_low]):
                val = nib | self._lsb
                req_write_high = pack(">B", val | FLAG_DATA_ENABLE)
                req_write_low = pack(">B", val & ~FLAG_DATA_ENABLE)

                self.i2c.write(req_write_low)

                self.i2c.write(req_write_high)
                self.i2c.readinto(response_buf, start=idx)

                self.i2c.write(req_write_low)

        response = unpack(">BB", response_buf)
        response_nib_high = response[0] & 0b11110000
        response_nib_low = (response[1] & 0b11110000) >> 4
        response_byte = response_nib_high + response_nib_low

        return response_byte
