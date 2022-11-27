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
# and ScopeDog or ServoCat as the telescope drive system.
# Optional is an Adafruit 2x16 line LCD with integrated buttons
# It requires astrometry.net installed
# It requires Skyfield

import subprocess
import time
import os
import sys
import glob
import math
from HandpadDebug import HandpadDebug
from NexusDebug import NexusDebug
from PIL import Image, ImageTk, ImageDraw, ImageOps
from PIL.Image import Resampling
import tkinter as tk
from tkinter import Label, Radiobutton, StringVar, Checkbutton, Button, Frame
import select
import re
from skyfield.api import load, Star, wgs84
from pathlib import Path
import fitsio
from fitsio import FITS, FITSHDR
import threading
import Nexus
import Coordinates
import Display
import logging
import argparse
from platesolve import PlateSolve
from common import Common
import utils

# comment out if this is the autoboot program
os.system("pkill -9 -f eFinder.py")

cwd_path: Path = Path.cwd() 
images_path: Path = Path("/dev/shm/images")
utils.create_path(images_path) # create dir if it doesn't yet exist

deltaAz = deltaAlt = 0
scope_x = scope_y = 0
d_x_str = d_y_str = "0"
image_height = 960
image_width = 1280
offset_new = offset_saved = offset = offset_reset = (0, 0)
align_count = 0
report = {
    "N": "Not tracking",
    "T": "Tracking",
    "A": "AltAz mode",
    "P": "EQ Mode",
    "G": "GEM mode",
    "0": "not aligned",
    "1": "1-star aligned   ",
    "2": "2-star aligned   ",
    "3": "3-star aligned   ",
}
solved = False
box_list = ["", "", "", "", "", ""]
eye_piece = []
radec = "no_radec"
f_g = "red"
b_g = "black"
solved_radec = 0, 0
usb = False
pix_scale = 15

# GUI specific
def setup_sidereal():
    global LST, lbl_LST, lbl_UTC, lbl_date, ts, nexus, window
    t = ts.now()
    LST = t.gmst + nexus.get_long() / 15  # as decimal hours
    LSTstr = (
        str(int(LST))
        + "h "
        + str(int((LST * 60) % 60))
        + "m "
        + str(int((LST * 3600) % 60))
        + "s"
    )
    lbl_LST = Label(window, bg=b_g, fg=f_g, text=LSTstr)
    lbl_LST.place(x=55, y=44)
    lbl_UTC = Label(window, bg=b_g, fg=f_g, text=t.utc_strftime("%H:%M:%S"))
    lbl_UTC.place(x=55, y=22)
    lbl_date = Label(window, bg=b_g, fg=f_g, text=t.utc_strftime("%d %b %Y"))
    lbl_date.place(x=55, y=0)


# GUI specific
def sidereal():
    global LST
    t = ts.now()
    LST = t.gmst + nexus.get_long() / 15  # as decimal hours
    LSTstr = (
        str(int(LST))
        + "h "
        + str(int((LST * 60) % 60))
        + "m "
        + str(int((LST * 3600) % 60))
        + "s"
    )
    lbl_LST.config(text=LSTstr)
    lbl_UTC.config(text=t.utc_strftime("%H:%M:%S"))
    lbl_date.config(text=t.utc_strftime("%d %b %Y"))
    lbl_LST.after(1000, sidereal)




def readNexus():
    """Read the AltAz from the Nexus DSC and put the correct numbers on the GUI."""
    nexus.read_altAz(None)
    nexus_radec = nexus.get_radec()
    nexus_altaz = nexus.get_altAz()
    tk.Label(
        window,
        width=10,
        text=coordinates.hh2dms(nexus_radec[0]),
        anchor="e",
        bg=b_g,
        fg=f_g,
    ).place(x=225, y=804)
    tk.Label(
        window,
        width=10,
        anchor="e",
        text=coordinates.dd2dms(nexus_radec[1]),
        bg=b_g,
        fg=f_g,
    ).place(x=225, y=826)
    tk.Label(
        window,
        width=10,
        anchor="e",
        text=coordinates.ddd2dms(nexus_altaz[1]),
        bg=b_g,
        fg=f_g,
    ).place(x=225, y=870)
    tk.Label(
        window,
        width=10,
        anchor="e",
        text=coordinates.dd2dms(nexus_altaz[0]),
        bg=b_g,
        fg=f_g,
    ).place(x=225, y=892)


def capture():
    global polaris, m31, radec, gain, exposure, platesolve, camera, camera_debug
    use_camera = camera
    extras = {}
    if polaris.get() == "1":
        extras['testimage'] = 'polaris'
        use_camera = camera_debug
    elif m31.get() == "1":
        extras['testimage'] = 'm31'
        use_camera = camera_debug
    radec = nexus.get_short()
    use_camera.capture(
        int(1000000 * float(exposure.get())),
        int(float(gain.get())),
        radec,
        extras
    )
    image_show()


def solveImage(is_offset=False):
    global scopeAlt, solved_altaz, star_name, star_name_offset, solved
    result, elapsed_time = platesolve.solve_image(is_offset)
    elapsed_time_str = f"elapsed time {elapsed_time:.2f} sec"

    tk.Label(window, text=elapsed_time_str, width=20, anchor="e", bg=b_g, fg=f_g).place(
        x=315, y=936
    )
    result = str(result.stdout)
    if "solved" not in result:
        solve_image_failed(b_g, f_g, elapsed_time, window)
        solved = False
        return
    if is_offset:
        table, h = fitsio.read(images_path / "capture.axy", header=True)
        star_name_offset = table[0][0], table[0][1]
        logging.debug(f'(capture.axy gives) x,y {table[0][0]} {table[0][1]}')
        if "The star" in result:
            lines = result.split("\n")
            for line in lines:
                print(line)
                if line.startswith("  The star "):
                    star_name = line.split(" ")[4]
                    logging.info(f"Solve-field Plot found: {star_name}")
                    box_write(star_name + " found", True)
                    break
        else:
            box_write(" no named star", True)
            logging.info("No Named Star found")
            star_name = "Unknown"
    solvedPos = common.applyOffset(nexus, offset)
    ra, dec, d = solvedPos.apparent().radec(ts.now())
    solved_radec = ra.hours, dec.degrees
    solved_altaz = coordinates.conv_altaz(nexus, *(solved_radec))
    scopeAlt = solved_altaz[0] * math.pi / 180
    solveImageGui(solved_radec, solved_altaz)
    solved = True
    box_write("solved", True)
    deltaCalcGUI()
    readTarget()

def solve_image_failed(b_g, f_g, elapsed_time, window):
    box_write("Solve Failed", True)
    tk.Label(
        window, width=10, anchor="e", text="no solution", bg=b_g, fg=f_g
    ).place(x=410, y=804)
    tk.Label(
        window, width=10, anchor="e", text="no solution", bg=b_g, fg=f_g
    ).place(x=410, y=826)
    tk.Label(
        window, width=10, anchor="e", text="no solution", bg=b_g, fg=f_g
    ).place(x=410, y=870)
    tk.Label(
        window, width=10, anchor="e", text="no solution", bg=b_g, fg=f_g
    ).place(x=410, y=892)
    tk.Label(window, text=elapsed_time, bg=b_g, fg=f_g).place(x=315, y=936)


def solveImageGui(solved_radec, solved_altaz):
    tk.Label(
        window,
        width=10,
        text=coordinates.hh2dms(solved_radec[0]),
        anchor="e",
        bg=b_g,
        fg=f_g,
    ).place(x=410, y=804)
    tk.Label(
        window,
        width=10,
        anchor="e",
        text=coordinates.dd2dms(solved_radec[1]),
        bg=b_g,
        fg=f_g,
    ).place(x=410, y=826)
    tk.Label(
        window,
        width=10,
        anchor="e",
        text=coordinates.ddd2dms(solved_altaz[1]),
        bg=b_g,
        fg=f_g,
    ).place(x=410, y=870)
    tk.Label(
        window,
        width=10,
        anchor="e",
        text=coordinates.dd2dms(solved_altaz[0]),
        bg=b_g,
        fg=f_g,
    ).place(x=410, y=892)

def image_show():
    global manual_angle, img3, EPlength, scopeAlt
    img2 = Image.open(images_path / "capture.jpg")
    width, height = img2.size
    img2 = img2.resize((1014, 760), Resampling.LANCZOS)  # original is 1280 x 960
    width, height = img2.size
    h = pix_scale * 960/60  # vertical finder field of view in arc min
    w = pix_scale * 1280/60
    w_offset = width * offset[0] * 60 / w 
    h_offset = height * offset[1] * 60 / h
    img2 = img2.convert("RGB")
    if grat.get() == "1":
        draw = ImageDraw.Draw(img2)
        draw.line([(width / 2, 0), (width / 2, height)], fill=75, width=2)
        draw.line([(0, height / 2), (width, height / 2)], fill=75, width=2)
        draw.line(
            [(width / 2 + w_offset, 0), (width / 2 + w_offset, height)],
            fill=255,
            width=1,
        )
        draw.line(
            [(0, height / 2 - h_offset), (width, height / 2 - h_offset)],
            fill=255,
            width=1,
        )
    if EP.get() == "1":
        draw = ImageDraw.Draw(img2)
        tfov = (
            (float(EPlength.get()) * height /
             float(param["scope_focal_length"]))
            * 60
            / h
        ) / 2  # half tfov in pixels
        draw.ellipse(
            [
                width / 2 + w_offset - tfov,
                height / 2 - h_offset - tfov,
                width / 2 + w_offset + tfov,
                height / 2 - h_offset + tfov,
            ],
            fill=None,
            outline=255,
            width=1,
        )
    if lock.get() == "1":
        img2 = zoom_at(img2, w_offset, h_offset, 1)
    if zoom.get() == "1":
        img2 = zoom_at(img2, 0, 0, 2)
    if flip.get() == "1":
        img2 = ImageOps.flip(img2)
    if mirror.get() == "1":
        img2 = ImageOps.mirror(img2)
    if auto_rotate.get() == "1":
        img2 = img2.rotate(scopeAlt)
    elif manual_rotate.get() == "1":
        angle_deg = angle.get()
        img2 = img2.rotate(float(angle_deg))
    img3 = img2
    img2 = ImageTk.PhotoImage(img2)
    panel.configure(image=img2)
    panel.image = img2
    panel.place(x=200, y=5, width=1014, height=760)


def annotate_image():
    global img3, bright, hip, hd, abell, ngc, tycho2
    scale_low = str(pix_scale * 0.9 * 1.2)  # * 1.2 is because image has been resized for the display panel
    scale_high = str(pix_scale * 1.1 * 1.2)
    image_show()
    img3 = img3.save(images_path / "adjusted.jpg")
    # first need to re-solve the image as it is presented in the GUI, saved as 'adjusted.jpg'
    annotate_cmd = "solve-field --no-plots --new-fits none --solved none --match none --corr none \
            --rdls none --cpulimit 10 --temp-axy --overwrite --downsample 2 --no-remove-lines --uniformize 0 \
            --scale-units arcsecperpix --scale-low " + scale_low + " \
            --scale-high " + scale_high + " " + str(images_path / "adjusted.jpg")
    logging.debug(f"Annotating image with cmd: {annotate_cmd}")
    os.system(annotate_cmd)
    # now we can annotate the image adjusted.jpg
    opt1 = " " if bright.get() == "1" else " --no-bright"
    opt2 = (
        " --hipcat=/usr/local/astrometry/annotate_data/hip.fits --hiplabel"
        if hip.get() == "1"
        else " "
    )
    opt3 = (
        " --hdcat=/usr/local/astrometry/annotate_data/hd.fits"
        if hd.get() == "1"
        else " "
    )
    opt4 = (
        " --abellcat=/usr/local/astrometry/annotate_data/abell-all.fits"
        if abell.get() == "1"
        else " "
    )
    opt5 = (
        " --tycho2cat=/usr/local/astrometry/annotate_data/tycho2.kd"
        if tycho2.get() == "1"
        else " "
    )
    opt6 = " " if ngc.get() == "1" else " --no-ngc"
    try:  # try because the solve may have failed to produce adjusted.jpg
        cmd = 'python3 /usr/local/astrometry/lib/python/astrometry/plot/plotann.py \
                --no-grid --tcolor="orange" --tsize="14" --no-const' + opt1 + opt2 + opt3 + opt4 + opt5 + opt6 + " " \
                + " ".join([str(images_path / "adjusted.wcs"), str(images_path / "adjusted.jpg"), str(images_path / "adjusted_out.jpg")])
        logging.debug(f"plotann cmd: {cmd}")
        os.system(cmd)
    except:
        logging.debug("Exception during plotann")
        pass
    if os.path.exists(images_path / "adjusted_out.jpg") == True:
        img3 = Image.open(images_path / "adjusted_out.jpg")
        filelist = glob.glob(str(images_path / "adjusted*.*"))
        for filePath in filelist:
            try:
                os.remove(filePath)
            except:
                logging.error("problem while deleting file :", filePath)
        box_write("annotation successful", True)
        img4 = ImageTk.PhotoImage(img3)
        panel.configure(image=img4)
        panel.image = img4
        panel.place(x=200, y=5, width=1014, height=760)
    else:
        box_write("solve failure", True)
        return


def zoom_at(img, x, y, zoom):
    w, h = img.size
    dh = (h - (h / zoom)) / 2
    dw = (w - (w / zoom)) / 2
    img = img.crop((dw + x, dh - y, w - dw + x, h - dh - y))
    return img.resize((w, h), Image.LANCZOS)


def deltaCalcGUI():
    global deltaAz, deltaAlt, solved_altaz
    deltaAz, deltaAlt = common.deltaCalc(nexus.get_altAz(), solved_altaz, nexus.get_scope_alt(), deltaAz, deltaAlt)
    deltaAzstr = "{: .1f}".format(float(deltaAz)).ljust(8)[:8]
    deltaAltstr = "{: .1f}".format(float(deltaAlt)).ljust(8)[:8]
    tk.Label(window, width=10, anchor="e", text=deltaAzstr, bg=b_g, fg=f_g).place(
        x=315, y=870
    )
    tk.Label(window, width=10, anchor="e", text=deltaAltstr, bg=b_g, fg=f_g).place(
        x=315, y=892
    )

def moveScope(dAz, dAlt):
    azPulse = abs(dAz / float(param["azSpeed"]))  # seconds
    altPulse = abs(dAlt / float(param["altSpeed"]))
    logging.debug(
        "%s %.2f  %s  %.2f %s" % (
            "azPulse:", azPulse, "altPulse:", altPulse, "seconds")
    )
    nexus.write("#:RG#")  # set move speed to guide
    box_write("moving scope in Az", True)
    logging.info("moving scope in Az")
    if dAz > 0:  # if +ve move scope left
        nexus.write("#:Me#")
        time.sleep(azPulse)
        nexus.write("#:Q#")
    else:
        nexus.write("#:Mw#")
        time.sleep(azPulse)
        nexus.write("#:Q#")
    time.sleep(0.2)
    box_write("moving scope in Alt", True)
    logging.info("moving scope in Alt")
    nexus.write("#:RG#")
    if dAlt > 0:  # if +ve move scope down
        nexus.write("#:Ms#")
        time.sleep(altPulse)
        nexus.write("#:Q#")
    else:
        nexus.write("#:Mn#")
        time.sleep(altPulse)
        nexus.write("#:Q#")
    box_write("move finished", True)
    logging.info("move finished")
    time.sleep(1)


def align():  # sends the Nexus the solved RA & Dec (JNow) as an align or sync point. LX200 protocol.
    global align_count, p
    # readNexus()
    capture()
    solveImage()
    readNexus()
    if solved == False:
        return
    align_ra = ":Sr" + coordinates.dd2dms((solved_radec)[0]) + "#"
    align_dec = ":Sd" + coordinates.dd2aligndms((solved_radec)[1]) + "#"

    try:
        valid = nexus.get(align_ra)
        logging.info("sent align RA command:", align_ra)
        box_write("sent " + align_ra, True)
        if valid == "0":
            box_write("invalid position", True)
            tk.Label(window, text="invalid alignment").place(x=20, y=680)
            return
        valid = nexus.get(align_dec)
        logging.info("sent align Dec command:", align_dec)
        box_write("sent " + align_dec, True)
        if valid == "0":
            box_write("invalid position", True)
            tk.Label(window, text="invalid alignment").place(x=20, y=680)
            return
        reply = nexus.get(":CM#")
        logging.info(":CM#")
        box_write("sent :CM#", False)
        logging.info("reply: ", reply)
        p = nexus.get(":GW#")
        logging.info("Align status reply ", p[0:3])
        box_write("Align reply:" + p[0:3], False)
        align_count += 1
    except Exception as ex:
        logging.error(ex)
        box_write("Nexus error", True)
    tk.Label(window, text="align count: " + str(align_count), bg=b_g, fg=f_g).place(
        x=20, y=600
    )
    tk.Label(window, text="Nexus report: " +
             p[0:3], bg=b_g, fg=f_g).place(x=20, y=620)
    readNexus()
    deltaCalcGUI()


def measure_offset():
    global offset_new, scope_x, scope_y, star_name, solved
    logging.debug("Starting measure_offset for {star_name=}")
    readNexus()
    logging.debug("Read nexus")
    capture()
    logging.debug("Did capture")
    solveImage(is_offset=True)
    logging.debug("Solved image")
    if solved == False:
        box_write("solve failed", True)
        logging.debug("solve failed")
        return
    scope_x, scope_y = star_name_offset
    if star_name == "Unknown":  # display warning in red.
        tk.Label(window, width=8, text=star_name, anchor="w", bg=f_g, fg=b_g).place(
            x=115, y=470
        )
    else:
        tk.Label(window, width=8, text=star_name, anchor="w", bg=b_g, fg=f_g).place(
            x=115, y=470
        )
    box_write(star_name, True)
    d_x, d_y, dxstr_new, dystr_new = common.pixel2dxdy(scope_x, scope_y)
    logging.debug(f"Measured star with star name = {star_name} and {dxstr_new=} and {dystr_new}")
    offset_new = d_x, d_y
    tk.Label(
        window,
        text=dxstr_new + "," + dystr_new + "          ",
        width=9,
        anchor="w",
        bg=b_g,
        fg=f_g,
    ).place(x=110, y=450)


def use_new():
    global offset, offset_new
    offset = offset_new
    x_offset_new, y_offset_new, dxstr, dystr = common.dxdy2pixel(offset[0], offset[1])
    tk.Label(window, text=dxstr + "," + dystr, bg=b_g, fg=f_g, width=8).place(
        x=60, y=400
    )


def save_offset():
    global param
    param["d_x"], param["d_y"] = offset
    save_param()
    get_offset()
    box_write("offset saved", True)


def get_offset():
    x_offset_saved, y_offset_saved, dxstr_saved, dystr_saved = common.dxdy2pixel(
        float(param["d_x"]), float(param["d_y"])
    )
    tk.Label(
        window,
        text=dxstr_saved + "," + dystr_saved + "          ",
        width=9,
        anchor="w",
        bg=b_g,
        fg=f_g,
    ).place(x=110, y=520)


def use_loaded_offset():
    global offset
    x_offset_saved, y_offset_saved, dxstr, dystr = common.dxdy2pixel(
        float(param["d_x"]), float(param["d_y"])
    )
    offset = float(param["d_x"]), float(param["d_y"])
    tk.Label(window, text=dxstr + "," + dystr, bg=b_g, fg=f_g, width=8).place(
        x=60, y=400
    )


def reset_offset():
    global offset
    offset = offset_reset
    box_write("offset reset", True)
    tk.Label(window, text="0,0", bg=b_g, fg="red", width=8).place(x=60, y=400)


def read_nexus_and_capture():
    global handpad
    handpad.display("Get information from Nexus", "", "")
    readNexus()
    handpad.display("Capture image", "", "")
    capture()


def solve():
    readNexus()
    handpad.display("Solving image", "", "")
    solveImage()
    image_show()


def readTarget():
    global goto_radec, goto_altaz, goto_ra, goto_dec
    goto_ra = nexus.get(":Gr#")
    goto_dec = nexus.get(":Gd#")
    if (
         goto_ra[0:2] == "00" and goto_ra[3:5] == "00"
    ):  # not a valid goto target set yet.
        box_write("no GoTo target", True)
        return
    ra = goto_ra.split(":")
    dec = re.split(r"[:*]", goto_dec)
    print("goto RA & Dec", goto_ra, goto_dec)
    goto_radec = (float(ra[0]) + float(ra[1]) / 60 + float(ra[2]) / 3600), (
        float(dec[0]) + float(dec[1]) / 60 + float(dec[2]) / 3600
    )
    goto_altaz = coordinates.conv_altaz(nexus, *(goto_radec))
    tk.Label(
        window,
        width=10,
        text=coordinates.hh2dms(goto_radec[0]),
        anchor="e",
        bg=b_g,
        fg=f_g,
    ).place(x=605, y=804)
    tk.Label(
        window,
        width=10,
        anchor="e",
        text=coordinates.dd2dms(goto_radec[1]),
        bg=b_g,
        fg=f_g,
    ).place(x=605, y=826)
    tk.Label(
        window,
        width=10,
        anchor="e",
        text=coordinates.ddd2dms(goto_altaz[1]),
        bg=b_g,
        fg=f_g,
    ).place(x=605, y=870)
    tk.Label(
        window,
        width=10,
        anchor="e",
        text=coordinates.dd2dms(goto_altaz[0]),
        bg=b_g,
        fg=f_g,
    ).place(x=605, y=892)
    dt_Az = solved_altaz[1] - goto_altaz[1]
    if abs(dt_Az) > 180:
        if dt_Az < 0:
            dt_Az = dt_Az + 360
        else:
            dt_Az = dt_Az - 360
    # actually this is delta'x' in arcminutes
    dt_Az = 60 * (dt_Az * math.cos(scopeAlt))
    dt_Alt = solved_altaz[0] - goto_altaz[0]
    dt_Alt = 60 * (dt_Alt)  # in arcminutes
    dt_Azstr = "{: .1f}".format(float(dt_Az)).ljust(8)[:8]
    dt_Altstr = "{: .1f}".format(float(dt_Alt)).ljust(8)[:8]
    tk.Label(window, width=10, anchor="e", text=dt_Azstr, bg=b_g, fg=f_g).place(
        x=500, y=870
    )
    tk.Label(window, width=10, anchor="e", text=dt_Altstr, bg=b_g, fg=f_g).place(
        x=500, y=892
    )


def goto():
    global goto_ra, goto_dec
    readTarget()
    align()  # local sync scope to true RA & Dec
    if solved == False:
        box_write("solve failed", True)
        return
    nexus.write(":Sr" + goto_ra + "#")
    nexus.write(":Sd" + goto_dec + "#")
    reply = nexus.get(":MS#")
    time.sleep(0.1)
    box_write("moving scope", True)


def move():
    solveImage()
    image_show()
    if solved == False:
        box_write("no solution yet", True)
        return
    goto_ra = nexus.get(":Gr#").split(":")
    goto_dec = re.split(r"[:*]", nexus.get(":Gd#"))
    # not a valid goto target set yet.
    if goto_ra[0] == "00" and goto_ra[1] == "00":
        box_write("no GoTo target", True)
        return
    logging.info("goto RA & Dec", goto_ra, goto_dec)
    ra = float(goto_ra[0]) + float(goto_ra[1]) / 60 + float(goto_ra[2]) / 3600
    dec = float(goto_dec[0]) + float(goto_dec[1]) / \
        60 + float(goto_dec[2]) / 3600
    logging.info("lgoto radec", ra, dec)
    alt_g, az_g = coordinates.conv_altaz(nexus, ra, dec)
    logging.info("target Az Alt", az_g, alt_g)
    delta_Az = (az_g - solved_altaz[1]) * 60  # +ve move scope right
    delta_Alt = (alt_g - solved_altaz[0]) * 60  # +ve move scope up
    delta_Az_str = "{: .2f}".format(delta_Az)
    delta_Alt_str = "{: .2f}".format(delta_Alt)
    logging.info("deltaAz, deltaAlt:", delta_Az_str, delta_Alt_str)
    box_write("deltaAz : " + delta_Az_str, True)
    box_write("deltaAlt: " + delta_Alt_str, True)
    moveScope(delta_Az, delta_Alt)
    # could insert a new capture and solve?


def on_closing():
    save_param()
    handpad.display('Program closed', 'via VNCGUI', '')
    sys.exit()

def box_write(new_line, show_handpad):
    global handpad
    t = ts.now()
    for i in range(5, 0, -1):
        box_list[i] = box_list[i - 1]
    box_list[0] = (t.utc_strftime("%H:%M:%S ") + new_line).ljust(36)[:35]
    for i in range(0, 5, 1):
        tk.Label(window, text=box_list[i], bg=b_g, fg=f_g).place(x=1050, y=980 - i * 16)

def reader():
    global button
    while True:
        if handpad.get_box() in select.select([handpad.get_box()], [], [], 0)[0]:
            button = handpad.get_box().readline().decode("ascii").strip("\r\n")
            window.event_generate("<<OLED_Button>>")
        time.sleep(0.1)

def get_param(location=Path(cwd_path, "eFinder.config")):
    global eye_piece, param, expRange, gainRange
    logging.debug(f"Loading params from {location}")
    if os.path.exists(location) == True:
        with open(location) as h:
            for line in h:
                line = line.strip("\n").split(":")
                param[line[0]] = line[1]
                if line[0].startswith("Eyepiece"):
                    label, fl, afov = line[1].split(",")
                    eye_piece.append((label, float(fl), float(afov)))
                elif line[0].startswith("Exp_range"):
                    expRange = line[1].split(",")
                elif line[0].startswith("Gain_range"):
                    gainRange = line[1].split(",")

def save_param():
    global param, exposure, polaris, m31
    param["Exposure"] = exposure.get()
    param["Gain"] = gain.get()
    param["Test mode"] = polaris.get() or m31.get()
    with open(cwd_path / "eFinder.config", "w") as h:
        for key, value in param.items():
            h.write("%s:%s\n" % (key, value))


def do_button(event):
    global handpad, coordinates
    logging.debug(f"button event: {button}")
    if button == '21':
        handpad.display('Capturing image', '', '')
        read_nexus_and_capture()
        handpad.display('Solving image', '', '')
        solve()
        handpad.display('RA:  '+coordinates.hh2dms(solved_radec[0]), 'Dec:'+coordinates.dd2dms(
            solved_radec[1]), 'd:'+str(deltaAz)[:6]+','+str(deltaAlt)[:6])
    elif button == '17':  # up button
        handpad.display('Performing', '  align', '')
        align()
        handpad.display('RA:  '+coordinates.hh2dms(
            solved_radec[0]), 'Dec:'+coordinates.dd2dms(solved_radec[1]), 'Report:'+p)
    elif button == '19':  # down button
        handpad.display('Performing', '   GoTo++', '')
        goto()
        handpad.display('RA:  '+coordinates.hh2dms(solved_radec[0]), 'Dec:'+coordinates.dd2dms(
            solved_radec[1]), 'd:'+str(deltaAz)[:6]+','+str(deltaAlt)[:6])

 


def main(realHandpad, realNexus, fakeCamera):
    # main code starts here
    global nexus, ts, param, window, earth, test, handpad, coordinates, camera, camera_debug, polaris, m31, exposure, panel, zoom, rotate, auto_rotate, manual_rotate, gain, grat, EP, lock, flip, mirror, angle, go_to, pix_scale, platesolve, common, bright, hip, hd, abell, tycho2, ngc, version
    common = Common(cwd_path, images_path, pix_scale, "_VNC")
    version = common.get_version()
    logging.info(f"Starting eFinder version {version}...")
    handpad = Display.Handpad(version) if realHandpad else HandpadDebug()
    coordinates = Coordinates.Coordinates()
    nexus = Nexus.Nexus(handpad, coordinates) if realNexus else NexusDebug(handpad, coordinates)
    platesolve = PlateSolve(pix_scale, images_path)
    NexStr = nexus.get_nex_str()
    param = dict()
    get_param(cwd_path / "eFinder.config")
    logging.debug(f"{param=}")

    planets = load("de421.bsp")
    earth = planets["earth"]
    ts = load.timescale()
    nexus.read()
    camera_type = param["Camera Type"] if not fakeCamera else 'TEST'
    camera_debug = common.pick_camera('TEST', handpad, images_path)
    camera = common.pick_camera(camera_type, handpad, images_path)

    logging.debug(f"The chosen camera is {camera} with {dir(camera)=}")
    handpad.display('eFinder via VNC', 'Select: Solves', 'Up:Align Dn:GoTo',)
    # main program loop, using tkinter GUI
    window = tk.Tk()
    window.title("ScopeDog eFinder v" + version)
    window.geometry("1300x1000+100+10")
    window.configure(bg="black")
    window.bind("<<OLED_Button>>", do_button)
    setup_sidereal()

    sid = threading.Thread(target=sidereal)
    sid.daemon = True
    sid.start()

    button = ""

    scan = threading.Thread(target=reader)
    scan.daemon = True
    scan.start()

    tk.Label(window, text="Date", fg=f_g, bg=b_g).place(x=15, y=0)
    tk.Label(window, text="UTC", bg=b_g, fg=f_g).place(x=15, y=22)
    tk.Label(window, text="LST", bg=b_g, fg=f_g).place(x=15, y=44)
    tk.Label(window, text="Loc:", bg=b_g, fg=f_g).place(x=15, y=66)
    tk.Label(
        window,
        width=18,
        anchor="w",
        text=str(nexus.get_long()) + "\u00b0  " +
        str(nexus.get_lat()) + "\u00b0",
        bg=b_g,
        fg=f_g,
    ).place(x=55, y=66)
    img = Image.open(cwd_path / "splashscreen.jpeg")
    img = img.resize((1014, 760))
    img = ImageTk.PhotoImage(img)
    panel = tk.Label(window, highlightbackground="red",
                     highlightthickness=2, image=img)
    panel.place(x=200, y=5, width=1014, height=760)

    exposure = StringVar()
    exposure.set(param["Exposure"])
    exp_frame = Frame(window, bg="black")
    exp_frame.place(x=0, y=100)
    tk.Label(exp_frame, text="Exposure", bg=b_g, fg=f_g).pack(padx=1, pady=1)
    for i in range(len(expRange)):
        tk.Radiobutton(
            exp_frame,
            text=str(expRange[i]),
            bg=b_g,
            fg=f_g,
            width=7,
            activebackground="red",
            anchor="w",
            highlightbackground="black",
            value=float(expRange[i]),
            variable=exposure,
        ).pack(padx=1, pady=1)

    gain = StringVar()
    gain.set(param["Gain"])
    gain_frame = Frame(window, bg="black")
    gain_frame.place(x=80, y=100)
    tk.Label(gain_frame, text="Gain", bg=b_g, fg=f_g).pack(padx=1, pady=1)
    for i in range(len(gainRange)):
        tk.Radiobutton(
            gain_frame,
            text=str(gainRange[i]),
            bg=b_g,
            fg=f_g,
            width=7,
            activebackground="red",
            anchor="w",
            highlightbackground="black",
            value=float(gainRange[i]),
            variable=gain,
        ).pack(padx=1, pady=1)

    options_frame = Frame(window, bg="black")
    options_frame.place(x=20, y=270)
    polaris = StringVar()
    polaris.set("0")
    tk.Checkbutton(
        options_frame,
        text="Polaris image",
        width=13,
        anchor="w",
        highlightbackground="black",
        activebackground="red",
        bg=b_g,
        fg=f_g,
        variable=polaris,
    ).pack(padx=1, pady=1)
    m31 = StringVar()
    m31.set("0")
    tk.Checkbutton(
        options_frame,
        text="M31 image",
        width=13,
        anchor="w",
        highlightbackground="black",
        activebackground="red",
        bg=b_g,
        fg=f_g,
        variable=m31,
    ).pack(padx=1, pady=1)

    box_write("ccd is " + camera.get_cam_type(), False)
    box_write("Nexus " + NexStr, True)

    but_frame = Frame(window, bg="black")
    but_frame.place(x=25, y=650)
    tk.Button(
        but_frame,
        text="Align",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        highlightbackground="red",
        bd=0,
        height=2,
        width=10,
        command=align,
    ).pack(padx=1, pady=40)
    tk.Button(
        but_frame,
        text="Capture",
        activebackground="red",
        highlightbackground="red",
        bd=0,
        bg=b_g,
        fg=f_g,
        height=2,
        width=10,
        command=read_nexus_and_capture,
    ).pack(padx=1, pady=5)
    tk.Button(
        but_frame,
        text="Solve",
        activebackground="red",
        highlightbackground="red",
        bd=0,
        height=2,
        width=10,
        bg=b_g,
        fg=f_g,
        command=solve,
    ).pack(padx=1, pady=5)
    tk.Button(
        but_frame,
        text="GoTo: via Align",
        activebackground="red",
        highlightbackground="red",
        bd=0,
        height=2,
        width=10,
        bg=b_g,
        fg=f_g,
        command=goto,
    ).pack(padx=1, pady=5)
    tk.Button(
        but_frame,
        text="GoTo: via Move",
        activebackground="red",
        highlightbackground="red",
        bd=0,
        height=2,
        width=10,
        bg=b_g,
        fg=f_g,
        command=move,
    ).pack(padx=1, pady=5)

    off_frame = Frame(window, bg="black")
    off_frame.place(x=10, y=420)
    tk.Button(
        off_frame,
        text="Measure",
        activebackground="red",
        highlightbackground="red",
        bd=0,
        height=1,
        width=8,
        bg=b_g,
        fg=f_g,
        command=measure_offset,
    ).pack(padx=1, pady=1)
    tk.Button(
        off_frame,
        text="Use New",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        highlightbackground="red",
        bd=0,
        height=1,
        width=8,
        command=use_new,
    ).pack(padx=1, pady=1)
    tk.Button(
        off_frame,
        text="Save Offset",
        activebackground="red",
        highlightbackground="red",
        bd=0,
        bg=b_g,
        fg=f_g,
        height=1,
        width=8,
        command=save_offset,
    ).pack(padx=1, pady=1)
    tk.Button(
        off_frame,
        text="Use Saved",
        activebackground="red",
        highlightbackground="red",
        bd=0,
        bg=b_g,
        fg=f_g,
        height=1,
        width=8,
        command=use_loaded_offset,
    ).pack(padx=1, pady=1)
    tk.Button(
        off_frame,
        text="Reset Offset",
        activebackground="red",
        highlightbackground="red",
        bd=0,
        bg=b_g,
        fg=f_g,
        height=1,
        width=8,
        command=reset_offset,
    ).pack(padx=1, pady=1)
    d_x, d_y, dxstr, dystr = common.pixel2dxdy(offset[0], offset[1])

    tk.Label(window, text="Offset:", bg=b_g, fg=f_g).place(x=10, y=400)
    tk.Label(window, text="0,0", bg=b_g, fg=f_g, width=6).place(x=60, y=400)

    nex_frame = Frame(window, bg="black")
    nex_frame.place(x=250, y=766)
    tk.Button(
        nex_frame,
        text="Nexus",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        highlightbackground="red",
        bd=0,
        command=readNexus,
    ).pack(padx=1, pady=1)

    tk.Label(window, text="delta x,y", bg=b_g, fg=f_g).place(x=345, y=770)
    tk.Label(window, text="Solution", bg=b_g, fg=f_g).place(x=435, y=770)
    tk.Label(window, text="delta x,y", bg=b_g, fg=f_g).place(x=535, y=770)
    target_frame = Frame(window, bg="black")
    target_frame.place(x=620, y=766)
    tk.Button(
        target_frame,
        text="Target",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        highlightbackground="red",
        bd=0,
        command=readTarget,
    ).pack(padx=1, pady=1)

    dis_frame = Frame(window, bg="black")
    dis_frame.place(x=800, y=765)
    tk.Button(
        dis_frame,
        text="Display",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        anchor="w",
        highlightbackground="red",
        bd=0,
        width=8,
        command=image_show,
    ).pack(padx=1, pady=1)
    grat = StringVar()
    grat.set("0")
    tk.Checkbutton(
        dis_frame,
        text="graticule",
        width=10,
        anchor="w",
        highlightbackground="black",
        activebackground="red",
        bg=b_g,
        fg=f_g,
        variable=grat,
    ).pack(padx=1, pady=1)
    lock = StringVar()
    lock.set("0")
    tk.Checkbutton(
        dis_frame,
        text="Scope centre",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        anchor="w",
        highlightbackground="black",
        bd=0,
        width=10,
        variable=lock,
    ).pack(padx=1, pady=1)
    zoom = StringVar()
    zoom.set("0")
    tk.Checkbutton(
        dis_frame,
        text="zoom x2",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        anchor="w",
        highlightbackground="black",
        bd=0,
        width=10,
        variable=zoom,
    ).pack(padx=1, pady=1)
    flip = StringVar()
    flip.set("0")
    tk.Checkbutton(
        dis_frame,
        text="flip",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        anchor="w",
        highlightbackground="black",
        bd=0,
        width=10,
        variable=flip,
    ).pack(padx=1, pady=1)
    mirror = StringVar()
    mirror.set("0")
    tk.Checkbutton(
        dis_frame,
        text="mirror",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        anchor="w",
        highlightbackground="black",
        bd=0,
        width=10,
        variable=mirror,
    ).pack(padx=1, pady=1)
    auto_rotate = StringVar()
    auto_rotate.set("0")
    tk.Checkbutton(
        dis_frame,
        text="auto-rotate",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        anchor="w",
        highlightbackground="black",
        bd=0,
        width=10,
        variable=auto_rotate,
    ).pack(padx=1, pady=1)
    manual_rotate = StringVar()
    manual_rotate.set("1")
    tk.Checkbutton(
        dis_frame,
        text="rotate angle",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        anchor="w",
        highlightbackground="black",
        bd=0,
        width=10,
        variable=manual_rotate,
    ).pack(padx=1, pady=1)
    angle = StringVar()
    angle.set("0")
    tk.Entry(
        dis_frame,
        textvariable=angle,
        bg="red",
        fg=b_g,
        highlightbackground="red",
        bd=0,
        width=5,
    ).pack(padx=10, pady=1)


    ann_frame = Frame(window, bg="black")
    ann_frame.place(x=950, y=765)
    tk.Button(
        ann_frame,
        text="Annotate",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        anchor="w",
        highlightbackground="red",
        bd=0,
        width=6,
        command=annotate_image,
    ).pack(padx=1, pady=1)
    bright = StringVar()
    bright.set("0")
    tk.Checkbutton(
        ann_frame,
        text="Bright",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        anchor="w",
        highlightbackground="black",
        bd=0,
        width=8,
        variable=bright,
    ).pack(padx=1, pady=1)
    hip = StringVar()
    hip.set("0")
    tk.Checkbutton(
        ann_frame,
        text="Hip",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        anchor="w",
        highlightbackground="black",
        bd=0,
        width=8,
        variable=hip,
    ).pack(padx=1, pady=1)
    hd = StringVar()
    hd.set("0")
    tk.Checkbutton(
        ann_frame,
        text="H-D",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        anchor="w",
        highlightbackground="black",
        bd=0,
        width=8,
        variable=hd,
    ).pack(padx=1, pady=1)
    ngc = StringVar()
    ngc.set("0")
    tk.Checkbutton(
        ann_frame,
        text="ngc/ic",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        anchor="w",
        highlightbackground="black",
        bd=0,
        width=8,
        variable=ngc,
    ).pack(padx=1, pady=1)
    abell = StringVar()
    abell.set("0")
    tk.Checkbutton(
        ann_frame,
        text="Abell",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        anchor="w",
        highlightbackground="black",
        bd=0,
        width=8,
        variable=abell,
    ).pack(padx=1, pady=1)
    tycho2 = StringVar()
    tycho2.set("0")
    tk.Checkbutton(
        ann_frame,
        text="Tycho2",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        anchor="w",
        highlightbackground="black",
        bd=0,
        width=8,
        variable=tycho2,
    ).pack(padx=1, pady=1)

    tk.Label(window, text="RA", bg=b_g, fg=f_g).place(x=200, y=804)
    tk.Label(window, text="Dec", bg=b_g, fg=f_g).place(x=200, y=826)
    tk.Label(window, text="Az", bg=b_g, fg=f_g).place(x=200, y=870)
    tk.Label(window, text="Alt", bg=b_g, fg=f_g).place(x=200, y=892)

    EP = StringVar()
    EP.set("0")
    EP_frame = Frame(window, bg="black")
    EP_frame.place(x=1060, y=770)
    rad13 = Checkbutton(
        EP_frame,
        text="FOV indicator",
        bg=b_g,
        fg=f_g,
        activebackground="red",
        anchor="w",
        highlightbackground="black",
        bd=0,
        width=20,
        variable=EP,
    ).pack(padx=1, pady=2)
    global EPlength
    EPlength = StringVar()
    EPlength.set(float(param["default_eyepiece"]))
    for i in range(len(eye_piece)):
        tk.Radiobutton(
            EP_frame,
            text=eye_piece[i][0],
            bg=b_g,
            fg=f_g,
            activebackground="red",
            anchor="w",
            highlightbackground="black",
            bd=0,
            width=20,
            value=eye_piece[i][1] * eye_piece[i][2],
            variable=EPlength,
        ).pack(padx=1, pady=0)
    get_offset()
    window.protocol("WM_DELETE_WINDOW", on_closing)
    window.mainloop()


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.basicConfig(
        format="%(asctime)s %(name)s: %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="eFinder")
    parser.add_argument(
        "-fh", "--fakehandpad", help="Use a fake handpad", default=False, action='store_true', required=False
    )
    parser.add_argument(
        "-fn", "--fakenexus", help="Use a fake nexus", default=False, action='store_true', required=False
    )
    parser.add_argument(
        "-fc", "--fakecamera", help="Use a fake camera", default=False, action='store_true', required=False
    )
    parser.add_argument(
        "-x", "--verbose", help="Set logging to debug mode", action="store_true"
    )
    args = parser.parse_args()
    # add the handlers to the logger
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    main(not args.fakehandpad, not args.fakenexus, args.fakecamera)
