from pathlib import Path
import time
import subprocess
import logging


class PlateSolve:
    def __init__(self, pix_scale, images_path: Path=Path('/dev/shm/images'), cwd_path: Path=Path.cwd()) -> None:
        self.cwd_path: Path = cwd_path 
        self.images_path: Path = images_path
        self.scale_low = str(pix_scale * 0.9)
        self.scale_high = str(pix_scale * 1.1)
        self.limitOptions = [
            "--overwrite",  # overwrite any existing files
            "--skip-solved",  # skip any files we've already solved
            "--cpulimit",
            # limit to 10 seconds(!). We use a fast timeout here because this code is supposed to be fast
            "10",
        ]
        self.optimizedOptions = [
            "--downsample",
            "2",  # downsample 4x. 2 = faster by about 1.0 second; 4 = faster by 1.3 seconds
            # Saves ~1.25 sec. Don't bother trying to remove surious lines from the image
            "--no-remove-lines",
            "--uniformize",
            "0",  # Saves ~1.25 sec. Just process the image as-is
        ]
        self.scaleOptions = [
            "--scale-units",
            "arcsecperpix",  # next two params are in arcsecs. Supplying this saves ~0.5 sec
            "--scale-low",
            self.scale_low,  # See config above
            "--scale-high",
            self.scale_high,  # See config above
        ]
        self.fileOptions = [
            "--dir", self.images_path,
            "-m", self.images_path,
            "--new-fits", "none",  # Don't create a new fits
            "--solved", "none",  # Don't generate the solved output
            "--match", "none",  # Don't generate matched output
            # "--wcs", "none", # would like to turn this off, but we need to generate wcs for some advanced features which might be turned off...
            "--corr", "none",  # Don't generate .corr files
            "--rdls", "none",  # Don't generate the point list
            "--temp-axy" # We can't specify not to create the axy list, but we can write it to temp dir
        ]
        self.cmd = ["solve-field"]
        self.captureFile = self.images_path / "capture.jpg"
        self.options = (
            self.limitOptions + self.optimizedOptions +
            self.scaleOptions + self.fileOptions + [self.captureFile]
        )
        pass

    def solve_image(self, offset_flag):
        # global solved, scopeAlt, star_name, star_name_offset, solved_radec, solved_altaz
        name_that_star = ([]) if (offset_flag == True) else (["--no-plots"])
        # "--temp-axy" We can't specify not to create the axy list, but we can write it to /tmp
        start_time = time.time()
        result = subprocess.run(
            self.cmd + name_that_star + self.options, capture_output=True, text=True
        )
        elapsed_time = time.time() - start_time
        logging.debug(f"platesolve result is: {result}")
        logging.debug(f"platesolve command is: {self.cmd + name_that_star + self.options}")  
        logging.debug(f"Platesolve elapsed time is {elapsed_time:.2f}")
        return result, elapsed_time

