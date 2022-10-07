from pathlib import Path
from shutil import copyfile
import time
from CameraInterface import CameraInterface
import zwoasi as asi
import Display


class ASICamera(CameraInterface):
    """The camera class for ASI cameras.  Implements the CameraInterface interface."""

    def __init__(self, handpad: Display, param: dict, offset_flag: bool):
        """Initializes the ASI camera

        Parameters:
        handpad (Display): The link to the handpad
        param (dict): The parameters from the configuration file
        offset_flag (bool): The offset_flag"""

        self.home_path = str(Path.home())
        self.param = param
        self.offset_flag = offset_flag
        self.handpath = handpad

        # find a camera
        asi.init("/lib/zwoasi/armv7/libASICamera2.so")
        num_cameras = asi.get_num_cameras()
        if num_cameras == 0:
            self.handpad.display("Error:", "   no camera found", "")
            self.camType = "not found"
            print("camera not found")
            time.sleep(1)
        else:
            self.camType = "ZWO"
            cameras_found = asi.list_cameras()
            camera_id = 0
            self.initialize()
            self.handpad.display("ZWO camera found", "", "")
            print("camera found")
            time.sleep(1)

    def initialize(self):
        """Initializes the camera and set the needed control parameters"""
        global camera
        camera = asi.Camera(0)
        camera.set_control_value(
            asi.ASI_BANDWIDTHOVERLOAD, camera.get_controls()["BandWidth"]["MinValue"]
        )
        camera.disable_dark_subtract()
        camera.set_control_value(asi.ASI_WB_B, 99)
        camera.set_control_value(asi.ASI_WB_R, 75)
        camera.set_control_value(asi.ASI_GAMMA, 50)
        camera.set_control_value(asi.ASI_BRIGHTNESS, 50)
        camera.set_control_value(asi.ASI_FLIP, 0)
        camera.set_image_type(asi.ASI_IMG_RAW8)

    def capture(self, exposure_time: float, gain: float, radec: str):
        """Capture an image with the camera

        Parameters:
        exposure_time (float): The exposure time in seconds
        gain (float): The gain
        radec (str)"""
        if self.camType == "not found":
            self.handpad.display("camera not found")
            return

        timestr = time.strftime("%Y%m%d-%H%M%S")
        camera.set_control_value(asi.ASI_GAIN, gain)
        camera.set_control_value(asi.ASI_EXPOSURE, exposure_time)  # microseconds
        if self.param["Test mode"] == "1":
            if self.offset_flag == False:
                copyfile(
                    self.home_path + "/Solver/test.jpg",
                    self.home_path + "/Solver/images/capture.jpg",
                )
            else:
                copyfile(
                    self.home_path + "/Solver/polaris.jpg",
                    self.home_path + "/Solver/images/capture.jpg",
                )
                print("using Polaris")
        else:
            camera.capture(filename=self.home_path + "/Solver/images/capture.jpg")
            copyfile(
                self.home_path + "/Solver/images/capture.jpg",
                self.home_path + "/Solver/Stills/" + timestr + "_" + radec + ".jpg",
            )

        return

    def get_cam_type(self) -> str:
        """Return the type of the camera

        Returns:
        str: The type of the camera"""
        return self.camType
