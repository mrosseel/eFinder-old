from pathlib import Path
from shutil import copyfile
import logging
from typing import Dict
import Display
from CameraInterface import CameraInterface

class CameraDebug(CameraInterface):
    """All cameras should implement this interface.  The interface is used in the eFinder and eFinder_VNCGUI code"""

    def __init__(self, handpad: Display, images_path=Path('/dev/shm/images'), cwd_path=Path.cwd()) -> None:
        self.cwd_path: Path = cwd_path
        self.images_path: Path = images_path 

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
            copyfile(self.cwd_path / "testimages/m31.jpg", self.images_path / "capture.jpg")
        elif extras['testimage'] == 'polaris':
            logging.info("Capturing debug image of Polaris")
            self.copy_polaris()
        else:
            logging.warning("No debug image was selected, choosing polaris")
            self.copy_polaris()

    def copy_polaris(self):
        copyfile(self.cwd_path / "testimages/polaris.jpg", self.images_path / "capture.jpg")

    def get_cam_type(self) -> str:
        """Return the type of the camera

        Returns:
        str: The type of the camera"""
        return "TEST"
