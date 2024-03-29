#! /usr/bin/env python
# -*- coding: utf-8 -*-
# PTZ controlled by Sony Dual Shock 4 Controller
# by Kenny


"""
Pan and Tilt:
[pan speed] : 1(low speed) – 24(high speed)；
[tilt speed]: 1(low speed) – 20(high speed).

Zoom:
[action] including：zoomin，zoomout，zoomstop；
[zoom speed]: 0(low speed) – 7(high speed)。

Focus
[action] including：focusin，focusout，focusstop；
[focus speed]: 0(low speed) – 7(high speed)

Preset Position control：
[action] including：posset，poscall;
[positionnumber]: 0-89，100-254
"""


import os
import pprint

import contextlib
with contextlib.redirect_stdout(None):
    import pygame

import math
import control_cmd

os.environ['SDL_VIDEODRIVER'] = 'dummy'


class PS4Controller(object):
    """Class representing the PS4 controller. Pretty straightforward functionality."""

    controller = None
    axis_data = None
    button_data = None
    hat_data = None

    def init(self):
        """Initialize the joystick components"""

        pygame.init()
        pygame.joystick.init()
        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()

        self.ptz = control_cmd.PTZ()

    def listen(self):
        # init.
        if not self.axis_data:
            self.axis_data = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        if not self.button_data:
            self.button_data = {}
            for i in range(self.controller.get_numbuttons()):
                self.button_data[i] = False

        if not self.hat_data:
            self.hat_data = {}
            for i in range(self.controller.get_numhats()):
                self.hat_data[i] = (0, 0)

        """Listen for events to happen"""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.JOYAXISMOTION:
                    self.axis_data[event.axis] = int(event.value*10)
                elif event.type == pygame.JOYBUTTONDOWN:
                    self.button_data[event.button] = True
                elif event.type == pygame.JOYBUTTONUP:
                    self.button_data[event.button] = False
                elif event.type == pygame.JOYHATMOTION:
                    self.hat_data[event.hat] = event.value


            # (pan{0~24}, tilt{1~20}
            leftjoystick_pan = self.axis_data[0]
            leftjoystick_tilt = self.axis_data[1]
            rightjoystick_pan = self.axis_data[2]
            rightjoystick_tilt = self.axis_data[3]
            vv = math.floor(abs(leftjoystick_pan)/10 * 12)
            ww = math.floor(abs(leftjoystick_tilt))
            vv_r = math.floor(abs(rightjoystick_pan)/10 * 12)
            ww_r = math.floor(abs(rightjoystick_tilt))
            if self.button_data[5] == False:
                if vv != 0:
                    vv += 12
                if ww != 0:
                    ww += 10

                if vv_r != 0:
                    vv_r += 12
                if ww_r != 0:
                    ww_r += 10

            # p = 0(low) - 7(high)
            wide_speed = round((self.axis_data[5]+10)/20 * 7)
            tele_speed = round((self.axis_data[4]+10)/20 * 7)
            
            
            # drive
            if self.button_data[4]:
            # left joystick mode
                if (leftjoystick_pan != 0 and leftjoystick_tilt != 0):
                    if leftjoystick_pan < 0 and leftjoystick_tilt < 0:
                        self.ptz.upleft(vv, ww)
                    elif leftjoystick_pan > 0 and leftjoystick_tilt < 0:
                        self.ptz.upright(vv, ww)
                    elif leftjoystick_pan < 0 and leftjoystick_tilt > 0:
                        self.ptz.downleft(vv, ww)
                    elif leftjoystick_pan > 0 and leftjoystick_tilt > 0:
                        self.ptz.downright(vv, ww)
                elif leftjoystick_pan != 0:
                    if leftjoystick_pan < 0:
                        self.ptz.left(vv, 0)
                    elif leftjoystick_pan > 0:
                        self.ptz.right(vv, 0)
                elif leftjoystick_tilt != 0:
                    if leftjoystick_tilt > 0:
                        self.ptz.down(0, ww)
                    elif leftjoystick_tilt < 0:
                        self.ptz.up(0, ww)
                else:
                    self.ptz.pt_stop(vv, ww)
            # separate mode
            else:
                if leftjoystick_pan != 0:
                    if leftjoystick_pan < 0:
                        self.ptz.left(vv, 0)
                    elif leftjoystick_pan > 0:
                        self.ptz.right(vv, 0)
                elif rightjoystick_tilt != 0:
                    if rightjoystick_tilt > 0:
                        self.ptz.down(0, ww_r)
                    elif rightjoystick_tilt < 0:
                        self.ptz.up(0, ww_r)
                elif leftjoystick_pan == 0 and rightjoystick_tilt == 0:
                    self.ptz.pt_stop(vv, ww)

            # zoom
            if tele_speed > 0:
                self.ptz.tele(tele_speed)
            elif wide_speed > 0:
                self.ptz.wide(wide_speed)
            elif tele_speed == 0 or wide_speed == 0:
                self.ptz.zoomstop()
            # home
            if self.button_data[12]:
                self.ptz.home()

            # set preset
            if self.button_data[5]:
                if self.button_data[0]:
                    self.ptz.setPreset(0)
                if self.button_data[1]:
                    self.ptz.setPreset(1)
                if self.button_data[2]:
                    self.ptz.setPreset(2)
                if self.button_data[3]:
                    self.ptz.setPreset(3)
            # call preset
            if self.button_data[0]:
                self.ptz.callPreset(0)
            elif self.button_data[1]:
                self.ptz.callPreset(1)
            elif self.button_data[2]:
                self.ptz.callPreset(2)
            elif self.button_data[3]:
                self.ptz.callPreset(3)

            # termination
            if self.button_data[8] and self.button_data[9]:
                del self.ptz
                exit()

            # cmd display
            print(' pan:{:02}, tilt:{:02}   wide:{}, tele:{}'.format(
                vv, ww, wide_speed, tele_speed), end='\r', flush=True)

if __name__ == "__main__":
    ps4 = PS4Controller()
    ps4.init()
    ps4.listen()
