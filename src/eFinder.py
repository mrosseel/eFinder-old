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

import subprocess
import time
import os
import math
from PIL import Image
import psutil
import re
from skyfield.api import Star
import numpy as np
import threading
import select
from pathlib import Path
import fitsio
import Nexus
import Coordinates
import Display
import ASICamera
from platesolve import PlateSolve
from common import Common
import utils

cwd_path: Path = Path.cwd() 
images_path: Path = Path("/dev/shm/images")
utils.create_path(images_path) # create dir if it doesn't yet exist
# os.system('pkill -9 -f eFinder.py') # stops the autostart eFinder program running
x = y = 0  # x, y  define what page the display is showing
deltaAz = deltaAlt = 0
increment = [0, 1, 5, 1, 1]
offset_flag = False
align_count = 0
offset = 640, 480
star_name = "no star"
solve = False
sync_count = 0
pix_scale = 15
platesolve = PlateSolve(pix_scale, images_path)
common = Common(cwd_path=cwd_path, images_path=images_path, pix_scale=pix_scale, version_suffix="")
version = common.get_version()

def imgDisplay():  # displays the captured image on the Pi desktop.
    for proc in psutil.process_iter():
        if proc.name() == "display":
            proc.kill()  # delete any previous image display
    im = Image.open(images_path / "capture.jpg")
    im.show()


def solveImage():
    global offset_flag, solve, solvedPos, elapsed_time, star_name, star_name_offset, solved_radec, solved_altaz
    handpad.display("Started solving", "", "")
    result, elapsed_time = platesolve.solve_image(offset_flag)
    result = str(result.stdout)
    if "solved" not in result:
        print("Bad Luck - Solve Failed")
        handpad.display("Not Solved", "", "")
        solve = False
        return
    if (offset_flag == True) and ("The star" in result):
        table, h = fitsio.read(cwd_path / "capture.axy", header=True)
        star_name_offset = table[0][0], table[0][1]
        lines = result.split("\n")
        for line in lines:
            if line.startswith("  The star "):
                star_name = line.split(" ")[4]
                print("Solve-field Plot found: ", star_name)
                break
    solvedPos = common.applyOffset(nexus, offset)
    ra, dec, d = solvedPos.apparent().radec(coordinates.get_ts().now())
    solved_radec = ra.hours, dec.degrees
    solved_altaz = coordinates.conv_altaz(nexus, *(solved_radec))
    nexus.set_scope_alt(solved_altaz[0] * math.pi / 180)
    arr[0, 2][0] = "Sol: RA " + coordinates.hh2dms(solved_radec[0])
    arr[0, 2][1] = "   Dec " + coordinates.dd2dms(solved_radec[1])
    arr[0, 2][2] = "time: " + str(elapsed_time)[0:4] + " s"
    solve = True
    deltaCalc()


def deltaCalc():
    global deltaAz, deltaAlt, solved_altaz, scopeAlt, elapsed_time
    deltaAz, deltaAlt = common.deltaCalc(nexus.get_altAz(), solved_altaz, nexus.get_scope_alt(), deltaAz, deltaAlt)
    deltaXstr = "{: .2f}".format(float(deltaAz))
    deltaYstr = "{: .2f}".format(float(deltaAlt))
    arr[0, 3][0] = "Delta: x= " + deltaXstr
    arr[0, 3][1] = "       y= " + deltaYstr
    arr[0, 3][2] = "time: " + str(elapsed_time)[0:4] + " s"


def align():
    global align_count, solve, sync_count, param, offset_flag, arr
    new_arr = nexus.read_altAz(arr)
    arr = new_arr
    capture()
    imgDisplay()
    solveImage()
    if solve == False:
        handpad.display(arr[x, y][0], "Solved Failed", arr[x, y][2])
        return
    align_ra = ":Sr" + coordinates.dd2dms((solved_radec)[0]) + "#"
    align_dec = ":Sd" + coordinates.dd2aligndms((solved_radec)[1]) + "#"
    valid = nexus.get(align_ra)
    print(align_ra)
    if valid == "0":
        print("invalid position")
        handpad.display(arr[x, y][0], "Invalid position", arr[x, y][2])
        return
    valid = nexus.get(align_dec)
    print(align_dec)
    if valid == "0":
        print("invalid position")
        handpad.display(arr[x, y][0], "Invalid position", arr[x, y][2])
        return
    reply = nexus.get(":CM#")
    print("reply: ", reply)
    p = nexus.get(":GW#")
    print("Align status reply ", p)
    align_count += 1
    if p != "AT2#":
        handpad.display(
            "'select' aligns",
            "align count: " + str(align_count),
            "Nexus reply: " + p[0:3],
        )
    else:
        if p == "AT2#":
            sync_count += 1
            handpad.display(
                "'select' syncs",
                "Sync count " + str(align_count),
                "Nexus reply " + p[0:3],
            )
            nexus.set_aligned(True)
    return


def measure_offset():
    global offset_str, offset_flag, param, scope_x, scope_y, star_name
    offset_flag = True
    handpad.display("started capture", "", "")
    capture()
    imgDisplay()
    solveImage()
    if solve == False:
        handpad.display("solve failed", "", "")
        return
    scope_x = star_name_offset[0]
    scope_y = star_name_offset[1]
    d_x, d_y, dxstr, dystr = common.pixel2dxdy(scope_x, scope_y)
    param["d_x"] = d_x
    param["d_y"] = d_y
    save_param()
    offset_str = dxstr + "," + dystr
    arr[0, 5][1] = "new " + offset_str
    arr[0, 6][1] = "new " + offset_str
    handpad.display(arr[0, 5][0], arr[0, 5][1], star_name + " found")
    offset_flag = False


def up_down(v):
    global x
    x = x + v
    handpad.display(arr[x, y][0], arr[x, y][1], arr[x, y][2])


def left_right(v):
    global y
    y = y + v
    handpad.display(arr[x, y][0], arr[x, y][1], arr[x, y][2])


def up_down_inc(i, sign):
    global increment
    arr[x, y][1] = int(float(arr[x, y][1])) + increment[i] * sign
    param[arr[x, y][0]] = float(arr[x, y][1])
    handpad.display(arr[x, y][0], arr[x, y][1], arr[x, y][2])
    update_summary()
    time.sleep(0.1)


def flip():
    global param
    arr[x, y][1] = 1 - int(float(arr[x, y][1]))
    param[arr[x, y][0]] = str((arr[x, y][1]))
    handpad.display(arr[x, y][0], arr[x, y][1], arr[x, y][2])
    update_summary()
    time.sleep(0.1)


def update_summary():
    global param
    arr[1, 0][0] = "Ex:" + str(param["Exposure"]) + "  Gn:" + str(param["Gain"])
    arr[1, 0][1] = "Test mode:" + str(param["Test mode"])
    save_param()


def capture():
    global param
    extras = {}
    if param["Test mode"] == "1":
        if offset_flag == False:
            extras['testimage'] = 'm13'
        else:
            extras['testimage'] = 'polaris'
    radec = nexus.get_short()
    camera.capture(
        int(float(param["Exposure"]) * 1000000),
        int(float(param["Gain"])),
        radec,
        extras
    )


def go_solve():
    global x, y, solve, arr
    new_arr = nexus.read_altAz(arr)
    arr = new_arr
    handpad.display("Image capture", "", "")
    capture()
    imgDisplay()
    handpad.display("Plate solving", "", "")
    solveImage()
    if solve == True:
        handpad.display("Solved", "", "")
    else:
        handpad.display("Not Solved", "", "")
        return
    x = 0
    y = 3
    handpad.display(arr[0, 3][0], arr[0, 3][1], arr[0, 3][2])


def goto():
    handpad.display("Attempting", "GoTo++", "")
    goto_ra = nexus.get(":Gr#")
    if (
        goto_ra[0:2] == "00" and goto_ra[3:5] == "00"
    ):  # not a valid goto target set yet.
        print("no GoTo target")
        return
    goto_dec = nexus.get(":Gd#")
    print("Target goto RA & Dec", goto_ra, goto_dec)
    align()
    if solve == False:
        handpad.display("problem", "solving", "")
        return
    nexus.write(":Sr" + goto_ra + "#")
    nexus.write(":Sd" + goto_dec + "#")
    reply = nexus.get(":MS#")
    handpad.display("Performing", " GoTo++", "")
    time.sleep(5)  # replace with a check on goto progress
    go_solve()


def reset_offset():
    global param, arr
    param["d_x"] = 0
    param["d_y"] = 0
    offset_str = "0,0"
    arr[0, 5][1] = "new " + offset_str
    arr[0, 6][1] = "new " + offset_str
    handpad.display(arr[x, y][0], arr[x, y][1], arr[x, y][2])
    save_param()


def get_param():
    global param, offset_str
    if os.path.exists(cwd_path / "eFinder.config") == True:
        with open(cwd_path / "eFinder.config") as h:
            for line in h:
                line = line.strip("\n").split(":")
                param[line[0]] = str(line[1])
        pix_x, pix_y, dxstr, dystr = common.dxdy2pixel(
            float(param["d_x"]), float(param["d_y"])
        )
        offset_str = dxstr + "," + dystr


def save_param():
    global param
    with open(cwd_path / "eFinder.config", "w") as h:
        for key, value in param.items():
            # print("%s:%s\n" % (key, value))
            h.write("%s:%s\n" % (key, value))


def reader():
    global button
    while True:
        if handpad.get_box() in select.select([handpad.get_box()], [], [], 0)[0]:
            button = handpad.get_box().readline().decode("ascii").strip("\r\n")
        time.sleep(0.1)


# main code starts here

# time.sleep(1)
handpad = Display.Handpad(version)
coordinates = Coordinates.Coordinates()
nexus = Nexus.Nexus(handpad, coordinates)
nexus.read()
param = dict()
get_param()

handpad.display("ScopeDog eFinder", "Ready", "")
# array determines what is displayed, computed and what each button does for each screen.
# [first line,second line,third line, up button action,down...,left...,right...,select button short press action, long press action]
# empty string does nothing.
# example: left_right(-1) allows left button to scroll to the next left screen
# button texts are infact def functions
p = ""
home = [
    "ScopeDog",
    "eFinder",
    "ver" + version,
    "",
    "up_down(1)",
    "",
    "left_right(1)",
    "go_solve()",
    "",
]
nex = [
    "Nex: RA ",
    "    Dec ",
    "",
    "",
    "",
    "left_right(-1)",
    "left_right(1)",
    "go_solve()",
    "goto()",
]
sol = [
    "No solution yet",
    "'select' solves",
    "",
    "",
    "",
    "left_right(-1)",
    "left_right(1)",
    "go_solve()",
    "goto()",
]
delta = [
    "Delta: No solve",
    "'select' solves",
    "",
    "",
    "",
    "left_right(-1)",
    "left_right(1)",
    "go_solve()",
    "goto()",
]
aligns = [
    "'Select' aligns",
    "not aligned yet",
    str(p),
    "",
    "",
    "left_right(-1)",
    "left_right(1)",
    "align()",
    "",
]
polar = [
    "'Select' Polaris",
    offset_str,
    "",
    "",
    "",
    "left_right(-1)",
    "left_right(1)",
    "measure_offset()",
    "",
]
reset = [
    "'Select' Resets",
    offset_str,
    "",
    "",
    "",
    "left_right(-1)",
    "",
    "reset_offset()",
    "",
]
summary = ["", "", "", "up_down(-1)", "", "", "left_right(1)", "go_solve()", ""]
exp = [
    "Exposure",
    param["Exposure"],
    "",
    "up_down_inc(1,1)",
    "up_down_inc(1,-1)",
    "left_right(-1)",
    "left_right(1)",
    "go_solve()",
    "goto()",
]
gn = [
    "Gain",
    param["Gain"],
    "",
    "up_down_inc(2,1)",
    "up_down_inc(2,-1)",
    "left_right(-1)",
    "left_right(1)",
    "go_solve()",
    "goto()",
]
mode = [
    "Test mode",
    int(param["Test mode"]),
    "",
    "flip()",
    "flip()",
    "left_right(-1)",
    "left_right(1)",
    "go_solve()",
    "goto()",
]
status = [
    "Nexus via " + nexus.get_nexus_link(),
    "Nex align " + str(nexus.is_aligned()),
    "Brightness",
    "",
    "",
    "left_right(-1)",
    "",
    "go_solve()",
    "goto()",
]

arr = np.array(
    [
        [home, nex, sol, delta, aligns, polar, reset],
        [summary, exp, gn, mode, status, status, status],
    ]
)
update_summary()
deg_x, deg_y, dxstr, dystr = common.dxdy2pixel(float(param["d_x"]), float(param["d_y"]))
offset_str = dxstr + "," + dystr
new_arr = nexus.read_altAz(arr)
arr = new_arr
if nexus.is_aligned() == True:
    arr[0, 4][1] = "Nexus is aligned"
    arr[0, 4][0] = "'Select' syncs"


camera = common.pick_camera(param["Camera Type"], handpad, images_path)

handpad.display("ScopeDog eFinder", "v" + version, "")
button = ""
# main program loop, scan buttons and refresh display

scan = threading.Thread(target=reader)
scan.daemon = True
scan.start()

while True:  # next loop looks for button press and sets display option x,y
    if button == "21":
        exec(arr[x, y][7])
    elif button == "20":
        exec(arr[x, y][8])
    elif button == "19":
        exec(arr[x, y][4])
    elif button == "17":
        exec(arr[x, y][3])
    elif button == "16":
        exec(arr[x, y][5])
    elif button == "18":
        exec(arr[x, y][6])
    button = ""
    time.sleep(0.1)
