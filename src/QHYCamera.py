from pathlib import Path
from shutil import copyfile
import time
from CameraInterface import CameraInterface
import Display
import cv2
import qhyccd
from ctypes import *
from typing import Dict
import utils

class QHYCamera(CameraInterface):
    """The camera class for ZWO cameras.  Implements the CameraInterface interface."""

    def __init__(self, handpad: Display, images_path=Path('/dev/shm/images'), home_path=Path.cwd()) -> None:
        """Initializes the QHY camera

        Parameters:
        handpad (Display): The link to the handpad"""

        self.home_path = home_path 
        self.images_path = images_path 
        self.stills_path: Path = home_path / "Stills"
        utils.create_path(self.stills_path) # create stills dir if not already therew
        self.handpad = handpad
        self.camType = "QHY"
        self.initialize()
        time.sleep(1)

    def initialize(self) -> None:
        """Initializes the camera and set the needed control parameters"""
        global camera
        if self.camType == "not found":
            return
        camera = qhyccd.qhyccd()
        ident = camera.connect(0x02).decode('UTF-8')[0:9]
        self.handpad.display("QHY camera found", ident, "")
        print('Found camera:',ident)

    def capture(
            self, exposure_time: float, gain: float, radec: str, extra: Dict 
    ) -> None:
        """Capture an image with the camera

        Parameters:
        exposure_time (float): The exposure time in seconds
        gain (float): The gain
        radec (str): The Ra and Dec
        m13 (bool): True if the example image of M13 should be used
        polaris (bool): True if the example image of Polaris should be used
        """
        if self.camType == "not found":
            self.handpad.display("camera not found", "", "")
            return

        timestr = time.strftime("%Y%m%d-%H%M%S")
        camera.SetGain(gain)
        camera.SetExposure(exposure_time/1000)  # milliseconds

        img = camera.GetSingleFrame()
        capture_path = self.images_path / "capture.jpg"
        cv2.imwrite(capture_path,img)
        copyfile(
            capture_path,
            self.stills_path / f"{timestr}_{radec}.jpg",
        )
        return

    def get_cam_type(self) -> str:
        """Return the type of the camera

        Returns:
        str: The type of the camera"""
        return self.camType
