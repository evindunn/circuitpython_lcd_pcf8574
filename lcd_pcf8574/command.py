# SPDX-FileCopyrightText: Copyright (c) 2022 Evin Dunn
# SPDX-License-Identifier: MIT

"""
Instructions for the HD44780 LCD driver
"""

try:
    from typing import Literal
except ImportError:
    pass


# pylint: disable=too-few-public-methods
class HD44780Instruction:
    """
    Class holding constant data and utility functions for the HD44780 LCD
    driver's instruction commands

    See page 24 of the datasheet: https://www.sparkfun.com/datasheets/LCD/HD44780.pdf
    """

    class Type:
        """
        Enum representing the type of instruction for the HD44780
        """

        DISPLAY_CLEAR = 0b00000001
        RETURN_HOME = 0b00000010
        ENTRY_MODE_SET = 0b00000100
        DISPLAY_CONTROL = 0b00001000
        CURSOR_DISPLAY_SHIFT = 0b00010000
        FUNCTION_SET = 0b00100000
        CGRAM_ADDR_SET = 0b01000000
        DDRAM_ADDR_SET = 0b10000000
        BUSY_FLAG_READ = 0b00000000

    class ArgsEntryModeSet:
        """
        Arguments for the ENTRY_MODE_SET instruction
        """

        INCREMENT_ADDRESS = 0b00000010
        SHIFT_DISPLAY = 0b00000001

    class ArgsDisplayControl:
        """
        Arguments for the DISPLAY_CONTROL instruction
        """

        DISPLAY_ON = 0b00000100
        CURSOR_ON = 0b00000010
        BLINK_ON = 0b00000001

    class ArgsCursorControl:
        """
        Arguments for the CURSOR_DISPLAY_SHIFT instruction
        """

        SHIFT_DISPLAY = 0b00001000
        SHIFT_RIGHT = 0b00000100

    class ArgsFunctionSet:
        """
        Arguments for the FUNCTION_SET instruction
        """

        DATA_LENGTH_8_BIT = 0b00010000
        MODE_2_LINE = 0b00001000
        FONT_5X10 = 0b00000100

    @staticmethod
    def clear_display() -> int:
        """
        Returns the op code for clearing the LCD
        """
        return HD44780Instruction.Type.DISPLAY_CLEAR

    @staticmethod
    def return_home() -> int:
        """
        Returns the op code for returning to row 0, column 0 of the LCD
        """
        return HD44780Instruction.Type.RETURN_HOME

    @staticmethod
    def entry_mode_set(address: Literal["increment", "decrement"], shift: bool) -> int:
        """
        :param address: Whether to increment or decrement the character address
            when new data is read/written
        :param shift: Whether to shift the display after this instruction is
            executed
        :return: The op code for setting the LCD's entry mode with the given
            arguments
        """
        val = HD44780Instruction.Type.ENTRY_MODE_SET
        if address == "increment":
            val |= HD44780Instruction.ArgsEntryModeSet.INCREMENT_ADDRESS
        if shift:
            val |= HD44780Instruction.ArgsEntryModeSet.SHIFT_DISPLAY
        return val

    @staticmethod
    def display_control(display_on: bool, cursor_on: bool, blink_on: bool) -> int:
        """
        :param display_on: Whether the display will show new data read/written
            to it
        :param cursor_on: Whether to display the cursor
        :param blink: Whether to show a blinking block cursor
        :return: The op code for setting the LCD's display settings with the
            given arguments
        """
        val = HD44780Instruction.Type.DISPLAY_CONTROL
        if display_on:
            val |= HD44780Instruction.ArgsDisplayControl.DISPLAY_ON
        if cursor_on:
            val |= HD44780Instruction.ArgsDisplayControl.CURSOR_ON
        if blink_on:
            val |= HD44780Instruction.ArgsDisplayControl.BLINK_ON
        return val

    @staticmethod
    def cursor_control(
        shift: Literal["cursor", "display"], direction: Literal["right", "left"]
    ) -> int:
        """
        :param shift: Whether to shift the cursor or display when a new
            character is entered
        :param direction: Whether to shift left or right
        :return: The op code for controlling the LCD's cursor with the given
            arguments
        """
        val = HD44780Instruction.Type.CURSOR_DISPLAY_SHIFT
        if shift == "display":
            val |= HD44780Instruction.ArgsCursorControl.SHIFT_DISPLAY
        if direction == "right":
            val |= HD44780Instruction.ArgsCursorControl.SHIFT_RIGHT
        return val

    @staticmethod
    def function_set(
        bits: Literal[8, 4], lines: Literal[2, 1], font: Literal["5x8", "5x10"]
    ) -> int:
        """
        :param bits: Whether the LCD should opperate in 4-bit or 8-bit mode
        :param lines: Whether the display has 1 or 2 lines
        :param font: Whether to use the 5x10 or 5x10 font
        :return: The op code for configuring the LCD with the given arguments
        """
        val = HD44780Instruction.Type.FUNCTION_SET
        if bits == 8:
            val |= HD44780Instruction.ArgsFunctionSet.DATA_LENGTH_8_BIT
        if lines == 2:
            val |= HD44780Instruction.ArgsFunctionSet.MODE_2_LINE
        if font == "5x10":
            val |= HD44780Instruction.ArgsFunctionSet.FONT_5X10
        return val

    @staticmethod
    def cgram_address_set(address: int) -> int:
        """
        :param address: Set the character memory address to the given value
        :return: The op code for setting the cgram address to the given
            value
        """
        return HD44780Instruction.Type.CGRAM_ADDR_SET | address

    @staticmethod
    def ddram_address_set(address: int) -> int:
        """
        :param address: Set the display memory address to the given value
        :return: The op code for setting the cgram address to the given
            value
        """
        return HD44780Instruction.Type.DDRAM_ADDR_SET | address

    @staticmethod
    def read_busy_flag() -> int:
        """
        :return: The op code for reading the busy flag of the LCD
        """
        return HD44780Instruction.Type.BUSY_FLAG_READ
