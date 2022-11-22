import subprocess
import re
from skyfield.api import load, Star, wgs84
import math
from pathlib import Path


class Common:

    def __init__(self, cwd_path, images_path, pix_scale) -> None:
       self.home_path = cwd_path 
       self.images_path = images_path
       self.pix_scale = pix_scale
       self.ts = load.timescale()


    # returns the RA & Dec (J2000) corresponding to an image x,y pixel
    def xy2rd(self, x, y): 
        result = subprocess.run(
            [
                "wcs-xy2rd",
                "-w",
                Path(self.images_path, "capture.wcs"),
                "-x",
                str(x),
                "-y",
                str(y),
            ],
            capture_output=True,
            text=True,
        )
        result = str(result.stdout)
        line = result.split("RA,Dec")[1]
        ra, dec = re.findall("[-,+]?\d+\.\d+", line)
        return (float(ra), float(dec))


    # converts an image pixel x,y to a delta x,y in degrees.
    def pixel2dxdy(self, pix_x, pix_y):
        deg_x = (float(pix_x) - 640) * self.pix_scale / 3600  # in degrees
        deg_y = (480 - float(pix_y)) * self.pix_scale / 3600
        # +ve if finder is left of Polaris
        dxstr = "{: .1f}".format(float(60 * deg_x))
        dystr = "{: .1f}".format(
            float(60 * deg_y)
        )  # +ve if finder is looking below Polaris
        return (deg_x, deg_y, dxstr, dystr)

    def dxdy2pixel(self, dx, dy):
        pix_x = dx * 3600 / self.pix_scale + 640
        pix_y = 480 - dy * 3600 / self.pix_scale
        # +ve if finder is left of Polaris
        dxstr = "{: .1f}".format(float(60 * dx))
        # +ve if finder is looking below Polaris
        dystr = "{: .1f}".format(float(60 * dy))
        return (pix_x, pix_y, dxstr, dystr)

    # creates & returns a 'Skyfield star object' at the set offset and adjusted to Jnow
    def applyOffset(self, nexus, offset):  
        x_offset, y_offset, dxstr, dystr = self.dxdy2pixel(offset[0], offset[1])
        ra, dec = self.xy2rd(x_offset, y_offset)
        solved = Star(
            ra_hours=float(ra) / 15, dec_degrees=float(dec)
        )  # will set as J2000 as no epoch input
        solvedPos_scope = (
            # GUI uses ts.now(), eFinder uses coordinates.get_ts().now()
            nexus.get_location().at(self.ts.now()).observe(solved)
        )  # now at Jnow and current location
        return solvedPos_scope



    def deltaCalc(self, nexus_altaz, solved_altaz, scope_alt, delta_az, delta_alt):
        deltaAz = solved_altaz[1] - nexus_altaz[1]
        if abs(delta_az) > 180:
            if delta_az < 0:
                delta_az = delta_az + 360
            else:
                delta_az = delta_az - 360
        # print('cosine scopeAlt',math.cos(scope_alt))
        delta_az = 60 * (
            delta_az * math.cos(scope_alt)
        )  # actually this is delta'x' in arcminutes
        delta_alt = solved_altaz[0] - nexus_altaz[0]
        delta_alt = 60 * (delta_alt)  # in arcminutes
        return delta_az, delta_alt 

    def pick_camera(self, camera_type, handpad, images_dir):
        camera = None
        if camera_type == 'ASI':
            import ASICamera
            camera = ASICamera.ASICamera(handpad, images_dir)
        elif camera_type == 'QHY':
            import QHYCamera
            camera = QHYCamera.QHYCamera(handpad)
        elif camera_type == 'TEST':
            import CameraDebug
            camera = CameraDebug.CameraDebug(images_dir)
        return camera

