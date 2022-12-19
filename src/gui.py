from skyfield.api import load, Star, wgs84
import tkinter as tk
from tkinter import Label, Radiobutton, StringVar, Checkbutton, Button, Frame
from PIL import Image, ImageTk, ImageDraw, ImageOps
from pathlib import Path
from common import CameraSettings

class EFinderGUI():
    f_g = "red"
    b_g = "black"
    LST, lbl_LST, lbl_UTC, lbl_date, nexus, sidereal = None, None, None, None, None, None
    exposure = 1.0
    # planets and earth not used
    planets = load("de421.bsp")
    earth = planets["earth"]
    ts = load.timescale()
    window = tk.Tk()

    def __init__(self, nexus, param, camera_settings: CameraSettings):
        self.nexus = nexus
        self.param = param
        self.camera_settings = camera_settings
        self.cwd_path: Path = Path.cwd()

    def update_nexus_GUI(self):
        """Put the correct nexus numbers on the GUI."""
        self.nexus.read_altAz(None)
        nexus_radec = self.nexus.get_radec()
        nexus_altaz = self.nexus.get_altAz()
        tk.Label(
            self.window,
            width=10,
            text=coordinates.hh2dms(nexus_radec[0]),
            anchor="e",
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=225, y=804)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=coordinates.dd2dms(nexus_radec[1]),
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=225, y=826)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=coordinates.ddd2dms(nexus_altaz[1]),
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=225, y=870)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=coordinates.dd2dms(nexus_altaz[0]),
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=225, y=892)

    def solve_image_failed(self, elapsed_time, b_g=None, f_g=None):
        self.box_write("Solve Failed", True)
        if b_g is None or f_g is None:
            b_g = self.b_g
            f_g = self.f_g
        tk.Label(
            self.window, width=10, anchor="e", text="no solution", bg=b_g, fg=f_g
        ).place(x=410, y=804)
        tk.Label(
            self.window, width=10, anchor="e", text="no solution", bg=b_g, fg=f_g
        ).place(x=410, y=826)
        tk.Label(
            self.window, width=10, anchor="e", text="no solution", bg=b_g, fg=f_g
        ).place(x=410, y=870)
        tk.Label(
            self.window, width=10, anchor="e", text="no solution", bg=b_g, fg=f_g
        ).place(x=410, y=892)
        tk.Label(self.window, text=elapsed_time,
                 bg=b_g, fg=f_g).place(x=315, y=936)

    def solve_image_success(self, solved_radec, solved_altaz):
        tk.Label(
            self.window,
            width=10,
            text=coordinates.hh2dms(solved_radec[0]),
            anchor="e",
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=410, y=804)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=coordinates.dd2dms(solved_radec[1]),
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=410, y=826)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=coordinates.ddd2dms(solved_altaz[1]),
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=410, y=870)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=coordinates.dd2dms(solved_altaz[0]),
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=410, y=892)

    def solve_elapsed_time(self, elapsed_time_str):
        tk.Label(self.window, text=elapsed_time_str, width=20, anchor="e", bg=self.b_g, fg=self.f_g).place(
            x=315, y=936)

    # GUI specific
    def setup_sidereal(self):
        # global LST, lbl_LST, lbl_UTC, lbl_date, ts, nexus, window
        b_g = self.b_g
        f_g = self.f_g
        t = self.ts.now()
        self.LST = t.gmst + self.nexus.get_long() / 15  # as decimal hours
        LSTstr = (
            str(int(self.LST))
            + "h "
            + str(int((self.LST * 60) % 60))
            + "m "
            + str(int((self.LST * 3600) % 60))
            + "s"
        )
        self.lbl_LST = Label(self.window, bg=b_g, fg=f_g, text=LSTstr)
        self.lbl_LST.place(x=55, y=44)
        self.lbl_UTC = Label(self.window, bg=b_g, fg=f_g,
                             text=t.utc_strftime("%H:%M:%S"))
        self.lbl_UTC.place(x=55, y=22)
        self.lbl_date = Label(self.window, bg=b_g, fg=f_g,
                              text=t.utc_strftime("%d %b %Y"))
        self.lbl_date.place(x=55, y=0)

    # GUI specific

    def sidereal(self):
        t = self.ts.now()
        self.LST = t.gmst + self.nexus.get_long() / 15  # as decimal hours
        LSTstr = (
            str(int(LST))
            + "h "
            + str(int((LST * 60) % 60))
            + "m "
            + str(int((LST * 3600) % 60))
            + "s"
        )
        self.lbl_LST.config(text=LSTstr)
        self.lbl_UTC.config(text=t.utc_strftime("%H:%M:%S"))
        self.lbl_date.config(text=t.utc_strftime("%d %b %Y"))
        self.lbl_LST.after(1000, self.sidereal)

    def set_window(self, window):
        self.window = window

################# the offset methods:

    def save_offset(self):
        global param
        param["d_x"], param["d_y"] = offset
        save_param()
        get_offset()
        eFinderGUI.box_write("offset saved", True)

    def get_offset(self):
        x_offset_saved, y_offset_saved, dxstr_saved, dystr_saved = common.dxdy2pixel(
            float(param["d_x"]), float(param["d_y"])
        )
        tk.Label(
            window,
            text=dxstr_saved + "," + dystr_saved + "          ",
            width=9,
            anchor="w",
            bg=eFinderGUI.b_g,
            fg=eFinderGUI.f_g,
        ).place(x=110, y=520)

    def use_saved_offset(self):
        global offset
        x_offset_saved, y_offset_saved, dxstr, dystr = common.dxdy2pixel(
            float(param["d_x"]), float(param["d_y"])
        )
        offset = float(param["d_x"]), float(param["d_y"])
        tk.Label(window, text=dxstr + "," + dystr, bg=b_g, fg=f_g, width=8).place(
            x=60, y=400
        )

    def use_new_offset(self):
        global offset, offset_new
        offset = offset_new
        x_offset_new, y_offset_new, dxstr, dystr = common.dxdy2pixel(
            offset[0], offset[1])
        tk.Label(window, text=dxstr + "," + dystr, bg=b_g, fg=f_g, width=8).place(
            x=60, y=400
        )

    def reset_offset(self):
        global offset
        offset = offset_reset
        eFinderGUI.box_write("offset reset", True)
        tk.Label(window, text="0,0", bg=b_g, fg="red", width=8).place(x=60, y=400)
###########################################

    def draw_screen(self, NexStr):
        b_g = self.b_g
        f_g = self.f_g
        tk.Label(self.window, text="Date", fg=f_g, bg=b_g).place(x=15, y=0)
        tk.Label(self.window, text="UTC", bg=b_g, fg=f_g).place(x=15, y=22)
        tk.Label(self.window, text="LST", bg=b_g, fg=f_g).place(x=15, y=44)
        tk.Label(self.window, text="Loc:", bg=b_g, fg=f_g).place(x=15, y=66)
        tk.Label(
            self.window,
            width=18,
            anchor="w",
            text=str(self.nexus.get_long()) + "\u00b0  " +
            str(self.nexus.get_lat()) + "\u00b0",
            bg=b_g,
            fg=f_g,
        ).place(x=55, y=66)
        img = Image.open(self.cwd_path / "splashscreen.jpeg")
        img = img.resize((1014, 760))
        img = ImageTk.PhotoImage(img)
        panel = tk.Label(self.window, highlightbackground="red",
                         highlightthickness=2, image=img)
        panel.place(x=200, y=5, width=1014, height=760)

        self.exposure_str: StringVar = StringVar()
        self.exposure_str.set(self.camera_settings.exposure])
        exp_frame = Frame(self.window, bg="black")
        exp_frame.place(x=0, y=100)
        tk.Label(exp_frame, text="Exposure", bg=b_g,
                 fg=f_g).pack(padx=1, pady=1)
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
                variable=self.exposure,
            ).pack(padx=1, pady=1)

        gain = StringVar()
        gain.set(self.camera_settings.gain)
        gain_frame = Frame(self.window, bg="black")
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
                variable=camera_settings.gain,
            ).pack(padx=1, pady=1)

        options_frame = Frame(self.window, bg="black")
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

        self.box_write("ccd is " + camera.get_cam_type(), False)
        self.box_write("Nexus " + NexStr, True)

        but_frame = Frame(self.window, bg="black")
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

        off_frame = Frame(self.window, bg="black")
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
            command=self.measure_offset,
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
            command=self.use_new_offset,
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
            command=self.save_offset,
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
            command=self.use_saved_offset,
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
            command=self.reset_offset,
        ).pack(padx=1, pady=1)
        d_x, d_y, dxstr, dystr = common.pixel2dxdy(offset[0], offset[1])

        tk.Label(self.window, text="Offset:", bg=b_g, fg=f_g).place(x=10, y=400)
        tk.Label(self.window, text="0,0", bg=b_g,
                 fg=f_g, width=6).place(x=60, y=400)

        nex_frame = Frame(self.window, bg="black")
        nex_frame.place(x=250, y=766)
        tk.Button(
            nex_frame,
            text="Nexus",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            highlightbackground="red",
            bd=0,
            command=self.readNexusGUI,
        ).pack(padx=1, pady=1)

        tk.Label(self.window, text="delta x,y", bg=b_g, fg=f_g).place(x=345, y=770)
        tk.Label(self.window, text="Solution", bg=b_g, fg=f_g).place(x=435, y=770)
        tk.Label(self.window, text="delta x,y", bg=b_g, fg=f_g).place(x=535, y=770)
        target_frame = Frame(self.window, bg="black")
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

        dis_frame = Frame(self.window, bg="black")
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

        ann_frame = Frame(self.window, bg="black")
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

        tk.Label(self.window, text="RA", bg=b_g, fg=f_g).place(x=200, y=804)
        tk.Label(self.window, text="Dec", bg=b_g, fg=f_g).place(x=200, y=826)
        tk.Label(self.window, text="Az", bg=b_g, fg=f_g).place(x=200, y=870)
        tk.Label(self.window, text="Alt", bg=b_g, fg=f_g).place(x=200, y=892)

        EP = StringVar()
        EP.set("0")
        EP_frame = Frame(self.window, bg="black")
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
        EPlength.set(float(self.param["default_eyepiece"]))
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
        self.window.protocol("WM_DELETE_WINDOW", on_closing)
        self.window.mainloop()

    def box_write(self, new_line, show_handpad):
        global handpad
        t = self.ts.now()
        for i in range(5, 0, -1):
            box_list[i] = box_list[i - 1]
        box_list[0] = (t.utc_strftime("%H:%M:%S ") + new_line).ljust(36)[:35]
        for i in range(0, 5, 1):
            tk.Label(self.window, text=box_list[i], bg=self.b_g, fg=self.f_g).place(
                x=1050, y=980 - i * 16)

    def deltaCalcGUI(self):
        global deltaAz, deltaAlt, solved_altaz
        deltaAz, deltaAlt = common.deltaCalc(
            nexus.get_altAz(), solved_altaz, nexus.get_scope_alt(), deltaAz, deltaAlt
        )
        deltaAzstr = "{: .1f}".format(float(deltaAz)).ljust(8)[:8]
        deltaAltstr = "{: .1f}".format(float(deltaAlt)).ljust(8)[:8]
        tk.Label(window, width=10, anchor="e", text=deltaAzstr, bg=b_g, fg=f_g).place(
            x=315, y=870
        )
        tk.Label(window, width=10, anchor="e", text=deltaAltstr, bg=b_g, fg=f_g).place(
            x=315, y=892
        )
