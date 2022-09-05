#!/usr/bin/python3

# Program to implement an eFinder (electronic finder) on motorised Alt Az telescopes
# Copyright (C) 2022 Keith Venables.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# This variant is customised for ZWO ASI ccds as camera, Nexus DSC as telescope interface
# It requires astrometry.net installed

import board
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd
import busio
import time
import serial


def display(line0, line1, line2):
    global LCD_module, USB_module
    if LCD_module == True:
        lcd.clear()
        lcd.message = line0+'\n'+line1
    if USB_module == True:
        box.write(bytes(('0:'+line0+'\n').encode('UTF-8')))
        box.write(bytes(('1:'+line1+'\n').encode('UTF-8')))
        box.write(bytes(('2:'+line2+'\n').encode('UTF-8')))

# main code starts here


i2c = busio.I2C(board.SCL, board.SDA)
lcd = character_lcd.Character_LCD_RGB_I2C(i2c, 16, 2)
lcd.color = [100, 0, 0]
LCD_module = True
time.sleep(2)

try:
    box = serial.Serial('/dev/ttyACM0',
                        baudrate=115200,
                        stopbits=serial.STOPBITS_ONE,
                        bytesize=serial.EIGHTBITS,
                        writeTimeout=0,
                        timeout=0,
                        rtscts=False,
                        dsrdtr=False)
    box.write(b'0:ScopeDog eFinder\n')
    box.write(b'1:eFinder found   \n')
    box.write(b'2:                \n')
    USB_module = True
except Exception as ex:
    USB_module = False

display('ScopeDog', 'eFinder v'+version, '')
print('LCD:', LCD_module, '  USB:', USB_module)


time.sleep(5)
