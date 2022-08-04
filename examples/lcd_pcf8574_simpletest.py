# SPDX-FileCopyrightText: Copyright (c) 2022 Evin Dunn
# SPDX-License-Identifier: MIT

from time import sleep

from board import GP0, GP1

from lcd_pcf8574 import LCD

LCD_COLUMNS = 16
LCD_ROWS = 2
LCD_ADDR = 0x27

SDA = GP0
SCL = GP1


def main():
    lcd = LCD(SDA, SCL, columns=LCD_COLUMNS, rows=LCD_ROWS, address=LCD_ADDR)
    lcd.blink(True)

    for char in "abcdefghijklmnopqrstuvwzyz" * 2:
        lcd.write(char)
        sleep(0.1)

    sleep(1)
    lcd.blink(False)

    sleep(1)
    lcd.cursor(False)

    sleep(1)
    lcd.write("!")

    sleep(1)
    lcd.clear()

    newmsg = "Done!"
    lcd.set_position(1, (LCD_COLUMNS - len(newmsg)) // 2)
    lcd.write(newmsg)

    while True:
        lcd.home()
        lcd.write(" " * 16)
        lcd.home()
        for char in "=" * 16:
            lcd.write(char)
            sleep(0.05)


if __name__ == "__main__":
    main()
