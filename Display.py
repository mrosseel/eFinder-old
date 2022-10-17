import time
import serial
import threading
import select


class Handpad:
    """All methods to work with the handpad"""

    def __init__(self, version: str) -> None:
        """Initialize the Handpad class, check if the handpad is an OLED or LCD display

        Parameters:
        version (str): The version of the eFinder software
        """
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
            self.LCD_module = False

        self.display("ScopeDog", "eFinder v" + self.version, "")
        print("LCD:", self.LCD_module, "  USB:", self.USB_module)

    def display(self, line0: str, line1: str, line2: str) -> None:
        """Display the three lines on the display

        Parameters:
        line0 (str): The first line to display
        line1 (str): The second line to display
        line2 (str): The third line to display.  This line is not displayed on the LCD module.
        """
        if self.LCD_module == True:
            self.lcd.clear()
            self.lcd.message = line0 + "\n" + line1
        if self.USB_module == True:
            self.box.write(bytes(("0:" + line0 + "\n").encode("UTF-8")))
            self.box.write(bytes(("1:" + line1 + "\n").encode("UTF-8")))
            self.box.write(bytes(("2:" + line2 + "\n").encode("UTF-8")))

    def get_box(self) -> serial.Serial:
        """Returns the box variable

        Returns:
        serial.Serial: The box variable"""
        return self.box

    def is_LCD_module(self) -> bool:
        """Return true if the handbox is an LCD

        Returns:
        bool: True is the handbox is an LCD"""
        return self.LCD_module

    def is_USB_module(self) -> bool:
        """Return true if the handbox is an OLED

        Returns:
        bool: True is the handbox is an OLED"""
        return self.USB_module

    def get_lcd(self):
        """Returns the LCD variable

        Returns:
        character_lcd.Character_LCD_RGB_I2C: The LCD variable"""
        return self.lcd
