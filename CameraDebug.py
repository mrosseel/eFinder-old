from pathlib import Path
from shutil import copyfile


class CameraDebug:
    """All cameras should implement this interface.  The interface is used in the eFinder and eFinder_VNCGUI code"""

    def initialize(self) -> None:
        """Initializes the camera and set the needed control parameters"""
        pass

    def capture(
        self, exposure_time: float, gain: float, radec: str, m13: bool, polaris: bool
    ) -> None:
        """Capture an image with the camera

        Parameters:
        exposure_time (float): The exposure time in seconds
        gain (float): The gain
        radec (str)"""
        cwd = Path.cwd()
        if m13 == True:
            copyfile(Path(cwd, "test.jpg"), Path(cwd, "capture.jpg"))
        elif polaris == True:
            copyfile(Path(cwd, "polaris.jpg"), Path(cwd, "capture.jpg"))
            print("using Polaris")

    def get_cam_type(self) -> str:
        """Return the type of the camera

        Returns:
        str: The type of the camera"""
        return "TEST"
