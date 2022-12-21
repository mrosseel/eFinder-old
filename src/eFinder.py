#!/usr/bin/python3

# Program to implement an eFinder (electronic finder) on motorised Alt Az telescopes
# Copyright (C) 2022 Keith Venables.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# This variant is customised for ZWO ASI ccds as camera, Nexus DSC as telescope interface
# It requires astrometry.net installed

import time
import os
import math
from PIL import Image
import psutil
import threading
import select
from pathlib import Path
import fitsio
from Nexus import Nexus
import Coordinates
from platesolve import PlateSolve
from common import Common
import utils
import logging
import argparse
from Display import Display, PrintOutput
from NexusDebug import NexusDebug
import logging
from handpad import HandPad
from common import CameraData, CLIData, AstroData, OffsetData
from typing import Tuple, Dict, List


version_string = "17_0"


class EFinder():

    def __init__(self, handpad: HandPad, common: Common,
                 camera_data: CameraData, cli_data: CLIData,
                 astro_data: AstroData, offset_data: OffsetData,
                 param: Dict):
        self.handpad = handpad
        self.camera_data = camera_data
        self.cli_data = cli_data
        self.astro_data = astro_data
        self.offset_data = offset_data
        self.cwd_path = Path.cwd()
        self.param = param
        self.common = common
        self.version = self.common.get_version()
        self.platesolve = PlateSolve(
            camera_data.pix_scale, self.cli_data.images_path)

    def align(self, nexus, offset_flag=False):
        # global align_count, solve, sync_count, param, offset_flag, arr
        nexus_ra, nexus_dec, is_aligned, _ = nexus.read_altAz()
        handpad.set_lines(handpad.nex,
                          f"Nex: RA {nexus_ra}", f"   Dec {nexus_dec}", None)
        if is_aligned:
            handpad.set_lines(handpad.aligns,
                              "'Select' syncs",
                              "Nexus is aligned", None)

        self.capture(offset_flag)
        self.imgDisplay()
        self.solveImage(offset_flag)
        cmd = self.handpad.get_current_cmd()
        if not self.astro_data.solved:
            output.display(cmd.line1, "Solved Failed", cmd.line3)
            return
        align_ra = ":Sr" + \
            coordinates.dd2dms((self.astro_data.solved_radec)[0]) + "#"
        align_dec = ":Sd" + \
            coordinates.dd2aligndms((self.astro_data.solved_radec)[1]) + "#"
        nexus_response = nexus.get(align_ra)
        logging.info(align_ra)
        if nexus_response == "0":
            logging.info("invalid position")
            output.display(cmd.line1, "Invalid position", cmd.line3)
            return
        nexus_response = nexus.get(align_dec)
        logging.info(align_dec)
        if nexus_response == "0":
            logging.info("invalid position")
            output.display(cmd.line1, "Invalid position", cmd.line3)
            return
        reply = nexus.get(":CM#")
        logging.info("reply: ", reply)
        p = nexus.get(":GW#")
        logging.info("Align status reply ", p)
        self.astro_data.align_count += 1
        if p != "AT2":
            output.display(
                "'select' aligns",
                "align count: " + str(self.astro_data.align_count),
                "Nexus reply: " + p[0:3],
            )
        else:
            if p == "AT2":
                self.astro_data.sync_count += 1
                output.display(
                    "'select' syncs",
                    "Sync count " + str(self.astro_data.align_count),
                    "Nexus reply " + p[0:3],
                )
                self.astro_data.nexus.set_aligned(True)
        return

    def capture(self, offset_flag=False):
        extras = {}
        if self.param["Test mode"] == "1":
            if offset_flag:
                extras['testimage'] = 'polaris'
            else:
                extras['testimage'] = 'm13'
        radec = nexus.get_short()
        self.camera_data.camera.capture(
            int(float(self.param["Exposure"]) * 1000000),
            int(float(self.param["Gain"])),
            radec,
            extras
        )

    def imgDisplay(self):  # displays the captured image on the Pi desktop.
        for proc in psutil.process_iter():
            if proc.name() == "display":
                proc.kill()  # delete any previous image display
        im = Image.open(self.cli_data.images_path / "capture.jpg")
        im.show()

    def solveImage(self, offset_flag=False):
        # global offset_flag, solve, solvedPos, elapsed_time, star_name, star_name_offset, solved_radec, solved_altaz
        output.display("Started solving", "", "")
        has_solved, has_star, star_name, _, elapsed_time = self.platesolve.solve_image(
            offset_flag)
        self.astro_data.solved = has_solved
        if not has_solved:
            logging.info("Bad Luck - Solve Failed")
            output.display("Not Solved", "", "")
            return
        if offset_flag and has_star:
            table, _ = fitsio.read(self.cwd_path / "capture.axy", header=True)
            self.offset_data.offset = table[0][0], table[0][1]
            self.offset_data.offset_star_name = star_name
        solvedPos = self.common.applyOffset(self.astro_data.nexus,
                                            self.offset_data.offset)
        ra, dec, d = solvedPos.apparent().radec(coordinates.get_ts().now())
        solved_radec = ra.hours, dec.degrees
        solved_altaz = coordinates.conv_altaz(
            self.astro_data.nexus, *(solved_radec))
        self.astro_data.solved_radec = solved_radec
        self.astro_data.solved_altaz = solved_altaz
        self.astro_data.nexus.set_scope_alt(solved_altaz[0] * math.pi / 180.0)
        handpad.set_lines(handpad.sol,
                          "Sol: RA " + coordinates.hh2dms(solved_radec[0]),
                          "   Dec " + coordinates.dd2dms(solved_radec[1]),
                          "time: " + str(elapsed_time)[0:4] + " s"
                          )
        self.deltaCalc(elapsed_time)

    def deltaCalc(self, elapsed_time):
        # global deltaAz, deltaAlt, solved_altaz, scopeAlt, elapsed_time
        deltaAz, deltaAlt = self.common.deltaCalc(
            self.astro_data.nexus.get_altAz(), self.astro_data.solved_altaz,
            self.astro_data.nexus.get_scope_alt(), self.astro_data.deltaAz,
            self.astro_data.deltaAlt)
        deltaXstr = "{: .2f}".format(float(deltaAz))
        deltaYstr = "{: .2f}".format(float(deltaAlt))
        handpad.set_lines(handpad.delta,
                          "Delta: x= " + deltaXstr,
                          "       y= " + deltaYstr,
                          "time: " + str(elapsed_time)[0:4] + " s"
                          )

    def measure_offset(self):
        # global self.offset_data.offset_str, offset_flag, param, scope_x, scope_y, star_name
        offset_flag = True
        output.display("started capture", "", "")
        self.capture(offset_flag)
        self.imgDisplay()
        self.solveImage(offset_flag)
        if not self.astro_data.solved:
            output.display("solve failed", "", "")
            return
        scope_x = self.offset_data.offset[0]
        scope_y = self.offset_data.offset[1]
        d_x, d_y, dxstr, dystr = self.common.pixel2dxdy(scope_x, scope_y)
        self.param["d_x"] = d_x
        self.param["d_y"] = d_y
        self.save_param()
        self.offset_data.offset_str = dxstr + "," + dystr
        self.handpad.set_lines(handpad.polar,
                               None, "new " + self.offset_data.offset_str, None)
        self.handpad.set_lines(handpad.reset,
                               None, "new " + self.offset_data.offset_str, None)
        cmd = self.handpad.get_cmd(self.handpad.polar)
        output.display(cmd.line1, cmd.line2,
                       f"{self.offset_data.offset_star_name} found")

    def go_solve(self):
        # global x, y, solve, arr
        nexus_ra, nexus_dec, is_aligned, _ = nexus.read_altAz()
        handpad.set_lines(handpad.nex,
                          f"Nex: RA {nexus_ra}", f"   Dec {nexus_dec}", None)
        output.display("Image capture", "", "")
        self.capture()
        self.imgDisplay()
        output.display("Plate solving", "", "")
        self.solveImage()
        if self.astro_data.solved:
            output.display("Solved", "", "")
        else:
            output.display("Not Solved", "", "")
            return
        self.handpad.set_pos(self.handpad.delta)
        self.handpad.display_array()

    def goto(self):
        nexus = self.astro_data.nexus
        output.display("Attempting", "GoTo++", "")
        goto_ra = nexus.get(":Gr#")
        if (
            goto_ra[0:2] == "00" and goto_ra[3:5] == "00"
        ):  # not a valid goto target set yet.
            logging.info("no GoTo target")
            return
        goto_dec = nexus.get(":Gd#")
        logging.info("Target goto RA & Dec", goto_ra, goto_dec)
        self.align(nexus)
        if not self.astro_data.solved:
            output.display("problem", "solving", "")
            return
        nexus.write(":Sr" + goto_ra + "#")
        nexus.write(":Sd" + goto_dec + "#")
        nexus.get(":MS#")
        output.display("Performing", " GoTo++", "")
        time.sleep(5)  # replace with a check on goto progress
        self.go_solve()

    def reset_offset(self):
        # global param, arr
        self.param["d_x"] = 0
        self.param["d_y"] = 0
        self.offset_data.offset_str = "0,0"
        self.handpad.set_lines(self.handpad.polar, None,
                               f"new {self.offset_data.offset_str}", None)
        self.handpad.set_lines(self.handpad.reset, None,
                               f"new {self.offset_data.offset_str}", None)
        self.handpad.display_array()
        self.save_param()

    def get_param(self):
        # global param, self.offset_data.offset_str
        if os.path.exists(self.cwd_path / "eFinder.config"):
            with open(self.cwd_path / "eFinder.config") as h:
                for line in h:
                    line = line.strip("\n").split(":")
                    param[line[0]] = str(line[1])
            _, _, dxstr, dystr = self.common.dxdy2pixel(
                float(param["d_x"]), float(param["d_y"])
            )
            self.offset_data.offset_str = dxstr + "," + dystr

    def save_param(self):
        # global param
        with open(self.cwd_path / "eFinder.config", "w") as h:
            for key, value in self.param.items():
                # logging.info("%s:%s\n" % (key, value))
                h.write("%s:%s\n" % (key, value))

    def reader(self):
        output = self.handpad.display
        while True:
            if output.get_box() in select.select([output.get_box()], [], [], 0)[0]:
                button = output.get_box().readline().decode("ascii").strip("\r\n")
                handpad.on_button(button)
            time.sleep(0.1)


# main code starts here
def main(cli_data: CLIData):
    logging.info(f"Options are: {cli_data}")
    output = Display() if cli_data.realHandpad else Display(PrintOutput())
    handpad = HandPad(output, version)
    coordinates = Coordinates.Coordinates()
    nexus: Nexus = Nexus(output, coordinates) if cli_data.real_nexus else NexusDebug(
        output, coordinates)
    nexus.read()
    common = Common(cwd_path=Path.cwd(),
                    images_path=cli_data.images_path,
                    pix_scale=camera_data.pix_scale,
                    version=version, version_suffix="")
    param = dict()
    get_param()

    output.display("ScopeDog eFinder", "Ready", "")
    update_summary()
    deg_x, deg_y, dxstr, dystr = common.dxdy2pixel(
        float(param["d_x"]), float(param["d_y"]))
    self.offset_data.offset_str = dxstr + "," + dystr
    new_arr = nexus.read_altAz(arr)
    arr = new_arr
    if nexus.is_aligned():
        handpad.set_lines(handpad.aligns,
                          "'Select' syncs",
                          "Nexus is aligned",
                          None)

    camera_type = param["Camera Type"] if not fakeCamera else 'TEST'
    camera_debug = common.pick_camera('TEST', output, images_path)
    camera = common.pick_camera(camera_type, output, images_path)

    output.display("ScopeDog eFinder", "v" + version, "")
    # main program loop, scan buttons and refresh display
    camera_data = CameraData(camera=camera,
                             camera_debug=camera_debug,
                             gain=1,
                             exposure=1,
                             pix_scale=15,
                             testimage="")
    astro_data = AstroData(nexus=nexus)
    offset_data = OffsetData()

    eFinder = EFinder(handpad, common, camera_data, cli_data,
                      astro_data, offset_data, param, temp_path)

    scan = threading.Thread(target=reader)
    scan.daemon = True
    scan.start()

    while True:  # next loop looks for button press and sets display option x,y
        time.sleep(0.1)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.basicConfig(
        format="%(asctime)s %(name)s: %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="eFinder")
    parser.add_argument(
        "-fh",
        "--fakehandpad",
        help="Use a fake handpad",
        default=False,
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-fn",
        "--fakenexus",
        help="Use a fake nexus",
        default=False,
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-fc",
        "--fakecamera",
        help="Use a fake camera",
        default=False,
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-g",
        "--hasgui",
        help="Show the GUI",
        default=False,
        action="store_true",
        required=False,
    )

    parser.add_argument(
        "-n",
        "--notmp",
        help="Don't use the /dev/shm temporary directory.\
                (usefull if not on pi)",
        default=False,
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-x", "--verbose", help="Set logging to debug mode", action="store_true"
    )
    parser.add_argument(
        "-l", "--log", help="Log to file", action="store_true"
    )
    args = parser.parse_args()
    # add the handlers to the logger
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.log:
        datenow = datetime.now()
        filehandler = f"efinder-{datenow:%Y%M%d-%H_%M_%S}.log"
        fh = logging.FileHandler(filehandler)
        fh.setLevel(logger.level)
        logger.addHandler(fh)

    if args.notmp:
        images_path = Path('/tmp')

    utils.create_path(images_path)  # create dir if it doesn't yet exist

    cli_data = CLIData(
        not args.fakehandpad, not args.fakecamera, not args.fakenexus,
        images_path, args.hasgui, [], [])
    main(cli_data)
