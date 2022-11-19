from pathlib import Path
import time
import subprocess
import logging


class PlateSolve:
    def __init__(self, pix_scale) -> None:
        self.home_path = str(Path.home())
        self.scale_low = str(pix_scale * 0.9)
        self.scale_high = str(pix_scale * 1.1)
        self.limitOptions = [
            "--overwrite",  # overwrite any existing files
            "--skip-solved",  # skip any files we've already solved
            "--cpulimit",
            # limit to 10 seconds(!). We use a fast timeout here because this code is supposed to be fast
            "5",
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
            "--new-fits",
            "none",  # Don't create a new fits
            "--solved",
            "none",  # Don't generate the solved output
            "--rdls",
            "none",  # Don't generate the point list
            "--match",
            "none",  # Don't generate matched output
            "--corr",
            "none",  # Don't generate .corr files
        ]
        self.cmd = ["solve-field"]
        self.captureFile = self.home_path + "/Solver/images/capture.jpg"
        self.options = (
            self.limitOptions + self.optimizedOptions +
            self.scaleOptions + self.fileOptions + [self.captureFile]
        )
        pass

    def solve_image(self):
        # global solved, scopeAlt, star_name, star_name_offset, solved_radec, solved_altaz
        name_that_star = ([]) if (offset_flag == True) else (["--no-plots"])
        # "--temp-axy" We can't specify not to create the axy list, but we can write it to /tmp
        start_time = time.time()
        result = subprocess.run(
            self.cmd + name_that_star + self.options, capture_output=True, text=True
        )
        elapsed_time = time.time() - start_time
        # print (result.stdout)
        logging.debug("Platesolve elapsed time is {elapsed_time:.2f}")
        return result, elapsed_time

