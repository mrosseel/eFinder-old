import time
import serial
import threading
import select


class Handpad:
    def __init__(self, version) -> None:
        self.version = version
        try:
            self.box = serial.Serial(
                "/dev/ttyACM0",
                baudrate=115200,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                writeTimeout=0,
                timeout=0,
                rtscts=False,
                dsrdtr=False,
            )
            self.box.write(b"0:ScopeDog eFinder\n")
            self.box.write(b"1:eFinder found   \n")
            if "VNC" in version:
                self.box.write(b"2:VNCGUI running  \n")
            else:
                self.box.write(b"2:                \n")

            self.USB_module = True
        except Exception as ex:
            self.USB_module = False

        try:
            import board
            import busio
            import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd

            i2c = busio.I2C(board.SCL, board.SDA)
            self.lcd = character_lcd.Character_LCD_RGB_I2C(i2c, 16, 2)
            self.lcd.color = [100, 0, 0]
            self.LCD_module = True
            time.sleep(2)
        except Exception as ex:
            print("no LCD setup", ex)
            self.LCD_module = False

        self.display("ScopeDog", "eFinder v" + self.version, "")
        print("LCD:", self.LCD_module, "  USB:", self.USB_module)

    def display(self, line0, line1, line2):
        if self.LCD_module == True:
            self.lcd.clear()
            self.lcd.message = line0 + "\n" + line1
        if self.USB_module == True:
            self.box.write(bytes(("0:" + line0 + "\n").encode("UTF-8")))
            self.box.write(bytes(("1:" + line1 + "\n").encode("UTF-8")))
            self.box.write(bytes(("2:" + line2 + "\n").encode("UTF-8")))

    def get_box(self):
        return self.box

    def is_LCD_module(self):
        return self.LCD_module

    def is_USB_module(self):
        return self.USB_module

    def get_lcd(self):
        return self.lcd
