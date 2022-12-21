import serial
import sys


class FakeBox():
    def readline(self):
        return ""


class Output():
    def display(self, line0: str, line1: str, line2: str) -> None:
        """Display the three lines on the display

        Parameters:
        line0 (str): The first line to display
        line1 (str): The second line to display
        line2 (str): The third line to display.  This line is not displayed on the LCD module.
        """
        pass

    def get_box(self):
        """Returns the box variable

        Returns:
        serial.Serial: The box variable"""
        pass


class SerialOutput(Output):
    box: serial.Serial

    def __init__(self, port="/dev/ttyACM0", baudrate=115200) -> None:
        try:
            self.box = serial.Serial(
                port,
                baudrate,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                writeTimeout=0,
                timeout=0,
                rtscts=False,
                dsrdtr=False,
            )
        except Exception as ex:
            print("ERROR: no handpad display box found")
            sys.exit()

    def display(self, line0: str, line1: str, line2: str) -> None:
        self.box.write(bytes(("0:" + line0 + "\n").encode("UTF-8")))
        self.box.write(bytes(("1:" + line1 + "\n").encode("UTF-8")))
        self.box.write(bytes(("2:" + line2 + "\n").encode("UTF-8")))


class PrintOutput:
    nr_chars = 20

    def __init__(self) -> None:
        self.header, header_dashes = self._create_headings(self.nr_chars, 'Handpad start')
        self.footer, _ = self._create_headings(self.nr_chars, 'Handpad stop', header_dashes)

    def _create_headings(self, nr_chars, text, header_dashes = None):
        dashes = int((nr_chars-len(text))/2) if header_dashes is None else header_dashes
        return f"{dashes*'-'}{text}{(nr_chars-dashes-len(text))*'-'}\n", dashes

    def display(self, line0: str, line1: str, line2: str) -> None:
        # no logging here because multiline logging is ugly 
        print(f"{self.header}{line0}\n{line1}\n{line2}\n{self.footer}")

    def get_box(self):
        return FakeBox()


class Display(Output):
    """All methods to work with the handpad"""
    output: Output

    def __init__(self, version: str, output: Output) -> None:
        """Initialize the Handpad class,

        Parameters:
        version (str): The version of the eFinder software
        """
        self.version = version
        self.output = output if output is not None else SerialOutput()
        self.display("eFinder", self.version, "")

    def display(self, line0: str, line1: str, line2: str) -> None:
        self.output.display(line0, line1, line2)

    def get_box(self):
        """Returns the box variable

        Returns:
        serial.Serial: The box variable"""
        return None
