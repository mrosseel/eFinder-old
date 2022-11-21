from pathlib import Path
from shutil import copyfile
import logging
from typing import Dict


class CameraDebug:
    """All cameras should implement this interface.  The interface is used in the eFinder and eFinder_VNCGUI code"""

    def __init__(self, images_dir):
        self.home = Path.home()
        self.images_dir = images_dir 

    def initialize(self) -> None:
        """Initializes the camera and set the needed control parameters"""
        pass

    def capture(
            self, exposure_time: float, gain: float, radec: str, extras: Dict
    ) -> None:
        """Capture an image with the camera

        Parameters:
        exposure_time (float): The exposure time in seconds
        gain (float): The gain
        radec (str)"""
        if extras['testimage'] == 'm31':
            logging.info("Capturing debug image of m31")
            copyfile(Path(self.home, "Solver/test.jpg"), Path(self.images_dir, "capture.jpg"))
        elif extras['testimage'] == 'polaris':
            logging.info("Capturing debug image of Polaris")
            self.copy_polaris()
        else:
            logging.warning("No debug image was selected, choosing polaris")
            self.copy_polaris()

    def copy_polaris(self):
        copyfile(Path(self.home, "Solver/polaris.jpg"),
                 Path(self.images_dir, "capture.jpg"))

    def get_cam_type(self) -> str:
        """Return the type of the camera

        Returns:
        str: The type of the camera"""
        return "TEST"
