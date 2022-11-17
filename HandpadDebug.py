import serial


class HandpadDebug():
    """ A fake handpad """
    module = False
    box = False # this is supposed to be a Serial object
    nr_chars = 20

    def __init__(self):
        self.header, header_dashes = self._create_headings(self.nr_chars, 'Handpad start')
        self.footer, _ = self._create_headings(self.nr_chars, 'Handpad stop', header_dashes)

    def display(self, line0: str, line1: str, line2: str) -> None:
        """Display the three lines on the display

        Parameters:
        line0 (str): The first line to display
        line1 (str): The second line to display
        line2 (str): The third line to display.  This line is not displayed on the LCD module.
        """
        # no logging here because multiline logging is ugly 
        print(f"{self.header}{line0}\n{line1}\n{line2}\n{self.footer}")

    def _create_headings(self, nr_chars, text, header_dashes = None):
        dashes = int((nr_chars-len(text))/2) if header_dashes is None else header_dashes
        return f"{dashes*'-'}{text}{(nr_chars-dashes-len(text))*'-'}\n", dashes

    def get_box(self) -> serial.Serial:
        """Returns the box variable

        Returns:
        serial.Serial: The box variable"""
        return self.box

    def is_USB_module(self) -> bool:
        """Return true if the handbox is an OLED

        Returns:
        bool: True is the handbox is an OLED"""
        return self.module
