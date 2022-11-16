

class NexusInterface:
    """The Nexus utility class"""

    def write(self, txt: str) -> None:
        """Write a message to the Nexus DSC

        Parameters:
        txt (str): The text to send to the Nexus DSC
        """
        print("sent", txt, "to Nexus")

    def get(self, txt: str) -> str:
        """Receive a message from the Nexus DSC

        Parameters:
        txt (str): The string to send (to tell the Nexus DSC what you want to receive)

        Returns:
        str:  The requested information from the DSC
        """
        pass

    def read(self) -> None:
        """Establishes that Nexus DSC is talking to us and get observer location and time data"""
        pass

    def read_altAz(self, arr):
        """Read the RA and declination from the Nexus DSC and convert them to altitude and azimuth

        Parameters:
        arr (np.array): The arr variable to show on the handpad

        Returns:
        np.array: The updated arr variable to show on the handpad
        """
        pass

    def get_short(self):
        """Returns a summary of RA & Dec for file labelling

        Returns:
        short: RADec
        """
        pass

    def get_location(self):
        """Returns the location on earth of the observer

        Returns:
        location: The location
        """
        pass

    def get_long(self):
        """Returns the longitude of the observer

        Returns:
        long: The lonogitude
        """
        pass

    def get_lat(self):
        """Returns the latitude of the observer

        Returns:
        lat: The latitude
        """
        pass

    def get_scope_alt(self):
        """Returns the altitude the telescope is pointing to

        Returns:
        The altitude
        """
        pass

    def get_altAz(self):
        """Returns the altitude and azimuth the telescope is pointing to

        Returns:
        The altitude and the azimuth
        """
        pass

    def get_radec(self):
        """Returns the RA and declination the telescope is pointing to

        Returns:
        The RA and declination
        """
        pass

    def get_nexus_link(self) -> str:
        """Returns how the Nexus DSC is connected to the eFinder

        Returns:
        str: How the Nexus DSC is connected to the eFidner
        """
        pass

    def get_nex_str(self) -> str:
        """Returns if the Nexus DSC is connected to the eFinder

        Returns:
        str: "connected" or "not connected"
        """
        pass

    def is_aligned(self) -> bool:
        """Returns if the Nexus DSC is connected to the eFinder

        Returns:
        bool: True if the Nexus DSC is connected to the eFidner, False otherwise.
        """
        pass

    def set_aligned(self, aligned: bool) -> None:
        """Set the connection status

        Parameters:
        bool: True if connected, False if not connected."""
        pass

    def set_scope_alt(self, scope_alt) -> None:
        """Set the altitude of the telescope.

        Parameters:
        scope_alt: The altitude of the telescope"""
        pass
