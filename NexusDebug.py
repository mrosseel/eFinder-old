from NexusInterface import NexusInterface
import serial
from skyfield.api import load, Star, wgs84
from datetime import datetime, timedelta
import Display
import Coordinates


class NexusDebug(NexusInterface):
    """The Nexus utility class"""

    radec = [0, 0]
    altaz = [0, 0]
    scope_alt = 42

    def __init__(self, handpad: Display, coordinates: Coordinates) -> None:
        """Initializes the Nexus DSC

        Parameters:
        handpad (Display): The handpad that is connected to the eFinder
        coordinates (Coordinates): The coordinates utility class to be used in the eFinder
        """
        self.handpad = handpad
        self.aligned = False
        self.nexus_link = "none"
        self.coordinates: Coordinates = coordinates
        self.NexStr = "not connected"
        self.short = "no_RADec"
        self.long = 42
        self.lat = 42

    def write(self, txt: str) -> None:
        """Write a message to the Nexus DSC

        Parameters:
        txt (str): The text to send to the Nexus DSC
        """
        pass

    def get(self, txt: str) -> str:
        """Receive a message from the Nexus DSC

        Parameters:
        txt (str): The string to send (to tell the Nexus DSC what you want to receive)

        Returns:
        str:  The requested information from the DSC
        """
        return "11:12:13"

    def read(self) -> None:
        """Establishes that Nexus DSC is talking to us and get observer location and time data"""
        self.location = self.coordinates.get_earth() + wgs84.latlon(self.lat, self.long)

    def read_altAz(self, arr):
        """Read the RA and declination from the Nexus DSC and convert them to altitude and azimuth

        Parameters:
        arr (np.array): The arr variable to show on the handpad

        Returns:
        np.array: The updated arr variable to show on the handpad
        """

    def get_short(self):
        """Returns a summary of RA & Dec for file labelling

        Returns:
        short: RADec
        """
        return self.short

    def get_location(self):
        """Returns the location on earth of the observer

        Returns:
        location: The location
        """
        return self.location

    def get_long(self):
        """Returns the longitude of the observer

        Returns:
        long: The lonogitude
        """
        return self.long

    def get_lat(self):
        """Returns the latitude of the observer

        Returns:
        lat: The latitude
        """
        return self.lat

    def get_scope_alt(self):
        """Returns the altitude the telescope is pointing to

        Returns:
        The altitude
        """
        return self.scope_alt

    def get_altAz(self):
        """Returns the altitude and azimuth the telescope is pointing to

        Returns:
        The altitude and the azimuth
        """
        return self.altaz

    def get_radec(self):
        """Returns the RA and declination the telescope is pointing to

        Returns:
        The RA and declination
        """
        return self.radec

    def get_nexus_link(self) -> str:
        """Returns how the Nexus DSC is connected to the eFinder

        Returns:
        str: How the Nexus DSC is connected to the eFidner
        """
        return self.nexus_link

    def get_nex_str(self) -> str:
        """Returns if the Nexus DSC is connected to the eFinder

        Returns:
        str: "connected" or "not connected"
        """
        return self.NexStr

    def is_aligned(self) -> bool:
        """Returns if the Nexus DSC is connected to the eFinder

        Returns:
        bool: True if the Nexus DSC is connected to the eFidner, False otherwise.
        """
        return self.aligned

    def set_aligned(self, aligned: bool) -> None:
        """Set the connection status

        Parameters:
        bool: True if connected, False if not connected."""
        self.aligned = aligned

    def set_scope_alt(self, scope_alt) -> None:
        """Set the altitude of the telescope.

        Parameters:
        scope_alt: The altitude of the telescope"""
        self.scope_alt = scope_alt
