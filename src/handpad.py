from Display import Display, DisplayButtons
from collections import namedtuple
import time
import logging
from typing import Dict


Pos = namedtuple('Pos', ['x', 'y'])
increment = [0, 1, 5, 1, 1]


class Commands:
    def __init__(self, line1, line2, line3, up, down, left, right, select, longselect):
        self.line1 = line1
        self.line2 = line2
        self.line3 = line3
        self.up = up
        self.down = down
        self.left = left
        self.right = right
        self.select = select
        self.longselect = longselect


class HandPad():

    Cmds = namedtuple('Commands', [
        'line1', 'line2', 'line3', 'up', 'down', 'left',
                          'right', 'select', 'longselect'])
    pos = Pos(x=0, y=0)
    offset_str = None
    nexus_tuple = ("", "")

    def __init__(self, display: Display, version: str, param: Dict) -> None:
        self.display = display
        self.p = ""  # TODO needs to be updated
        self.param = param

        self.home = Commands(
            line1="ScopeDog", line2="eFinder",
            line3="ver" + version, up="",
            down="self.up_down(1)",
            left="self.left_right(1)",
            right="", select="self.go_solve()", longselect=""
        )
        self.nex = Commands(
            line1="Nex: RA", line2="Dec", line3="", up="", down="",
            left="self.left_right(-1)", right="self.left_right(1)",
            select="self.go_solve()", longselect="self.goto()"
        )
        self.sol = Commands(
            line1="No solution yet", line2="'select' solves", line3="",
            up="", down="",
            left="self.left_right(-1)", right="self.left_right(1)",
            select="self.go_solve()", longselect="self.goto()"
        )
        self.delta = Commands(
            line1="Delta: No solve", line2="'select' solves", line3="",
            up="", down="",
            left="self.left_right(-1)", right="self.left_right(1)",
            select="self.go_solve()", longselect="self.goto()"
        )
        self.aligns = Commands(
            line1="'Select' aligns", line2="not aligned yet", line3=str(self.p),
            up="", down="",
            left="self.left_right(-1)", right="self.left_right(1)",
            select="align()", longselect=""
        )
        self.polar = Commands(
            line1="'Select' Polaris", line2=self.offset_str, line3="",
            up="", down="",
            left="self.left_right(-1)", right="self.left_right(1)",
            select="measure_offset()", longselect=""
        )
        self.reset = Commands(
            line1="'Select' Resets", line2=self.offset_str, line3="",
            up="", down="",
            left="self.left_right(-1)", right="",
            select="reset_offset()", longselect=""
        )
        self.summary = Commands(
            line1="", line2="", line3="", up="self.up_down(-1)", down="",
            left="", right="self.left_right(1)",
            select="self.go_solve()", longselect=""
        )
        self.exp = Commands(
            line1="Exposure", line2=self.param["Exposure"], line3="",
            up="self.up_down_inc(1,1)", down="self.up_down_inc(1,-1)",
            left="self.left_right(-1)", right="self.left_right(1)",
            select="self.go_solve()", longselect="self.goto()"
        )
        self.gn = Commands(
            line1="Gain", line2=self.param["Gain"], line3="",
            up="self.up_down_inc(2,1)", down="self.up_down_inc(2,-1)",
            left="self.left_right(-1)", right="self.left_right(1)",
            select="self.go_solve()", longselect="self.goto()")
        self.mode = Commands(
            line1="Test mode", line2=int(self.param["Test mode"]), line3="",
            up="flip()", down="flip()",
            left="self.left_right(-1)", right="self.left_right(1)",
            select="self.go_solve()", longselect="self.goto()")
        self.status = Commands(
            line1="Nexus via " + self.nexus_tuple[0],
            line2="Nex align " + self.nexus_tuple[1],
            line3="Brightness", up="", down="",
            left="self.left_right(-1)", right="",
            select="self.go_solve()", longselect="self.goto()")
        logging.info(f"self.mode = {self.mode}, {type(self.mode)}")
        self.arr = [
            [self.home, self.nex, self.sol, self.delta,
             self.aligns, self.polar, self.reset],
            [self.summary, self.exp, self.gn, self.mode,
             self.status, self.status, self.status],
        ]
        logging.info(f"self.arr[0][0] is {type(self.arr[0][0])}")
        self.nex_pos = Pos(0, 1)
        self.summary_pos = Pos(1, 0)
        self.sol_pos = Pos(0, 2)
        self.delta_pos = Pos(0, 3)
        self.aligns_pos = Pos(0, 4)
        self.polar_pos = Pos(0, 5)
        self.reset_pos = Pos(0, 6)

    def get(self, pos: Pos) -> Cmds:
        return self.arr[pos[0]][pos[1]]

    def set_lines(self, pos: Pos, line1, line2, line3):
        if line1 is not None:
            self.get(pos).line1 = line1
        if line2 is not None:
            self.get(pos).line2 = line2
        if line3 is not None:
            self.get(pos).line3 = line3
        # self.display.display(line1, line2, line3)

    def set_pos(self, pos: Pos):
        self.pos = pos

    def display_array(self):
        cmd: self.Cmds = self.get(self.pos)
        self.display.display(
            cmd.line1, cmd.line2, cmd.line3)

    def get_current_cmd(self) -> Cmds:
        return self.get_cmd(self.pos)

    def get_cmd(self, pos: Pos) -> Cmds:
        return self.get(pos)

    def on_button(self, button, param, offset_str, nexus_tuple):
        self.param = param
        self.offset_str = offset_str
        self.nexus_tuple = nexus_tuple
        if button == DisplayButtons.BTN_SELECT:
            return self.get(self.pos).select
        elif button == DisplayButtons.BTN_LONGSELECT:
            return self.get(self.pos).longselect
        elif button == DisplayButtons.BTN_UP:
            exec(self.get(self.pos).up)
        elif button == DisplayButtons.BTN_DOWN:
            exec(self.get(self.pos).down)
        elif button == DisplayButtons.BTN_LEFT:
            exec(self.get(self.pos).left)
        elif button == DisplayButtons.BTN_RIGHT:
            exec(self.get(self.pos).right)

    # array determines what is displayed, computed and what each button does for each screen.
    # [first line,second line,third line, up button action,down...,left...,right...,select button short press action, long press action]
    # empty string does nothing.
    # example: left_right(-1) allows left button to scroll to the next left screen
    # button texts are infact def functions

    def up_down(self, v):
        self.pos=Pos(self.pos.x+v, self.pos.y)
        self.display_array()

    def left_right(self, v):
        self.pos=Pos(self.pos.x, self.pos.y+v)
        self.display_array()

    def up_down_inc(self, i, sign):
        self.get(self.pos).line2=int(
            float(self.get(self.pos).line2)) + self.increment[i] * sign
        self.param[self.get(self.pos).line1]=float(self.get(self.pos).line2)
        self.display_array()
        self.update_summary()
        time.sleep(0.1)

    def flip(self):
        self.get(self.pos).line2=1 - int(float(self.get(self.pos).line2))
        self.param[self.get(self.pos).line1]=str((self.get(self.pos).line2))
        self.display_array()
        self.update_summary()
        time.sleep(0.1)

    def update_summary(self):
        self.arr[self.summary].line1=f'Ex:{str(self.param["Exposure"])}  Gn:{str(self.param["Gain"])}'
        self.arr[self.summary].line2=f'Test mode:{str(self.param["Test mode"])}'
        save_param()
