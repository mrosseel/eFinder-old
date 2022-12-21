from enum import Enum
from Display import Display
from collections import namedtuple
import numpy as np
import time

BTN_SELECT = 21
DO_SELECT = 7  # does solve mostly
BTN_LONGSELECT = 20
DO_LONGSELECT = 8
BTN_LEFT = 16
DO_LEFT = 5
BTN_RIGHT = 18
DO_RIGHT = 6
BTN_UP = 17
DO_UP = 3
BTN_DOWN = 19
DO_DOWN = 4

Pos = namedtuple('Pos', ['x', 'y'])
increment = [0, 1, 5, 1, 1]


class HandPad():

    Cmds = namedtuple('Commands', [
        'line1', 'line2', 'line3', 'up', 'down', 'left',
                          'right', 'select', 'longselect'])
    pos = Pos(x=0, y=0)

    def __init__(self, display: Display, version: str) -> None:
        self.display = display
        self.p = ""  # TODO needs to be updated

        self.home = self.Cmds(
            line1="ScopeDog", line2="eFinder",
            line3="ver" + version, up="",
            down="self.up_down(1)",
            left="self.left_right(1)",
            right="", select="self.go_solve()", longselect=""
        )
        self.nex = self.Cmds(
            line1="Nex: RA", line2="Dec", line3="", up="", down="",
            left="self.left_right(-1)", right="self.left_right(1)",
            select="self.go_solve()", longselect="self.goto()"
        )
        self.sol = self.Cmds(
            line1="No solution yet", line2="'select' solves", line3="",
            up="", down="",
            left="self.left_right(-1)", right="self.left_right(1)",
            select="self.go_solve()", longselect="self.goto()"
        )
        self.delta = self.Cmds(
            line1="Delta: No solve", line2="'select' solves", line3="",
            up="", down="",
            left="self.left_right(-1)", right="self.left_right(1)",
            select="self.go_solve()", longselect="self.goto()"
        )
        self.aligns = self.Cmds(
            line1="'Select' aligns", line2="not aligned yet", line3=str(self.p),
            up="", down="",
            left="self.left_right(-1)", right="self.left_right(1)",
            select="align()", longselect=""
        )
        self.polar = self.Cmds(
            line1="'Select' Polaris", line2=offset_str, line3="",
            up="", down="",
            left="self.left_right(-1)", right="self.left_right(1)",
            select="measure_offset()", longselect=""
        )
        self.reset = self.Cmds(
            line1="'Select' Resets", line2=offset_str, line3="",
            up="", down="",
            left="self.left_right(-1)", right="",
            select="reset_offset()", longselect="")
        self.summary = self.Cmds(
            line1="", line2="", line3="", up="self.up_down(-1)", down="",
            left="", right="self.left_right(1)",
            select="self.go_solve()", longselect="")
        self.exp = self.Cmds(
            line1="Exposure", line2=param["Exposure"], line3="",
            up="self.up_down_inc(1,1)", down="self.up_down_inc(1,-1)",
            left="self.left_right(-1)", right="self.left_right(1)",
            select="self.go_solve()", longselect="self.goto()")
        self.gn = self.Cmds(
            line1="Gain", line2=param["Gain"], line3="",
            up="self.up_down_inc(2,1)", down="self.up_down_inc(2,-1)",
            left="self.left_right(-1)", right="self.left_right(1)",
            select="self.go_solve()", longselect="self.goto()")
        self.mode = self.Cmds(
            line1="Test mode", line2=int(param["Test mode"]), line3="",
            up="flip()", down="flip()",
            left="self.left_right(-1)", right="self.left_right(1)",
            select="self.go_solve()", longselect="self.goto()")
        self.status = self.Cmds(
            line1="Nexus via " + nexus.get_nexus_link(),
            line2="Nex align " + str(nexus.is_aligned()),
            line3="Brightness", up="", down="",
            left="self.left_right(-1)", right="",
            select="self.go_solve()", longselect="self.goto()")
        self.arr = np.array(
            [
                [home, nex, sol, delta, aligns, polar, reset],
                [summary, exp, gn, mode, status, status, status],
            ]
        )
        self.nex = Pos(0, 1)
        self.summary = Pos(1, 0)
        self.sol = Pos(0, 2)
        self.delta = Pos(0, 3)
        self.aligns = Pos(0, 4)
        self.polar = Pos(0, 5)
        self.reset = Pos(0, 6)

    def set_lines(self, pos: Pos, line1, line2, line3):
        if line1 is not None:
            self.arr[pos].line1 = line1
        if line2 is not None:
            self.arr[pos].line2 = line2
        if line3 is not None:
            self.arr[pos].line3 = line3
        # self.display.display(line1, line2, line3)

    def set_pos(self, pos: Pos):
        self.pos = pos

    def display_array(self):
        self.display.display(
            self.arr[self.pos].line1, self.arr[self.pos].line2, self.arr[self.pos].line3)

    def get_current_cmd(self) -> Cmds:
        return self.get_cmd(self.pos)

    def get_cmd(self, pos: Pos) -> Cmds:
        return self.arr[pos]

    def on_button(self, button):
        if button == BTN_SELECT:
            exec(self.arr[self.pos][DO_SELECT])
        elif button == BTN_LONGSELECT:
            exec(self.arr[self.pos][DO_LONGSELECT])
        elif button == BTN_UP:
            exec(self.arr[self.pos][DO_UP])
        elif button == BTN_DOWN:
            exec(self.arr[self.pos][DO_DOWN])
        elif button == BTN_LEFT:
            exec(self.arr[self.pos][DO_LEFT])
        elif button == BTN_RIGHT:
            exec(self.arr[self.pos][DO_RIGHT])

    # array determines what is displayed, computed and what each button does for each screen.
    # [first line,second line,third line, up button action,down...,left...,right...,select button short press action, long press action]
    # empty string does nothing.
    # example: left_right(-1) allows left button to scroll to the next left screen
    # button texts are infact def functions

    def up_down(self, v):
        self.pos = Pos(self.pos.x+v, self.pos.y)
        self.display_array()

    def left_right(self, v):
        self.pos = Pos(self.pos.x, self.pos.y+v)
        self.display_array()

    def up_down_inc(self, i, sign):
        global increment
        self.arr[self.pos].line2 = int(
            float(self.arr[self.pos].line2)) + increment[i] * sign
        param[self.arr[self.pos].line1] = float(self.arr[self.pos].line2)
        self.display_array()
        update_summary()
        time.sleep(0.1)

    def flip(self):
        self.arr[self.pos].line2 = 1 - int(float(self.arr[self.pos].line2))
        param[self.arr[self.pos].line1] = str((self.arr[self.pos].line2))
        self.display_array()
        update_summary()
        time.sleep(0.1)

    def update_summary(self):
        self.arr[self.summary].line1 = f'Ex:{str(self.param["Exposure"])}  Gn:{str(self.param["Gain"])}'
        self.arr[self.summary].line2 = f'Test mode:{str(self.param["Test mode"])}'
        save_param()
