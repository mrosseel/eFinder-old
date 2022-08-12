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
import serial
import os
import math
from PIL import Image
import zwoasi as asi
from datetime import datetime, timedelta
import psutil
from shutil import copyfile
import socket
import re
from skyfield.api import load, Star, wgs84
import numpy as np
import threading
import select
from pathlib import Path

HOST = '10.0.0.1'
PORT = 4060
home_path = str(Path.home())
os.system('pkill -9 -f eFinder.py') # stops the autostart eFinder program running
version = '12_2_wifi'

def convAltaz(ra,dec): # decimal ra in hours, decimal dec.
    Rad = math.pi/180
    t=ts.now()
    LST = t.gmst+Long/15 #as decimal hours
    ra =ra * 15 # need to work in degrees now
    LSTd = LST * 15
    LHA = (LSTd - ra + 360) - ((int)((LSTd - ra + 360)/360))*360   
    x = math.cos(LHA * Rad) * math.cos(dec * Rad)
    y = math.sin(LHA * Rad) * math.cos(dec * Rad)
    z = math.sin(dec * Rad)    
    xhor = x * math.cos((90 - Lat) * Rad) - z * math.sin((90 - Lat) * Rad)
    yhor = y
    zhor = x * math.sin((90 - Lat) * Rad) + z * math.cos((90 - Lat) * Rad)
    az = math.atan2(yhor, xhor) * (180/math.pi) + 180
    alt = math.asin(zhor) * (180/math.pi)
    return(alt,az)

def dd2dms(dd): # converts Dec or Alt from signed decimal to D:M:S
    is_positive = dd >= 0
    dd = abs(dd)
    minutes,seconds = divmod(dd*3600,60)
    degrees,minutes = divmod(minutes,60)
    sign = '+' if is_positive else '-'  
    dms = '%s%02d:%02d:%02d' % (sign,degrees,minutes,seconds)
    return(dms)

def dd2aligndms(dd): # converts Dec or Alt from signed decimal to D*M:S with '*' as delimter (LX200 protocol)
    is_positive = dd >= 0
    dd = abs(dd)
    minutes,seconds = divmod(dd*3600,60)
    degrees,minutes = divmod(minutes,60)
    sign = '+' if is_positive else '-'  
    dms = '%s%02d*%02d:%02d' % (sign,degrees,minutes,seconds)
    return(dms)

def ddd2dms(dd): # converts Az from decimal to D:M:S
    minutes,seconds = divmod(dd*3600,60)
    degrees,minutes = divmod(minutes,60)
    dms = '%03d:%02d:%02d' % (degrees,minutes,seconds)
    return(dms)

def hh2dms(dd): # converts RA from decimal to D:M:S
    minutes,seconds = divmod(dd*3600,60)
    degrees,minutes = divmod(minutes,60)
    dms = '%02d:%02d:%02d' % (degrees,minutes,seconds)
    return(dms)

def rd2xy(ra,dec): #returns the camera pixel x,y of the given RA & Dec
    result = subprocess.run(["wcs-rd2xy","-w",home_path+"/Solver/images/capture.wcs","-r",str(ra),"-d",str(dec)],capture_output=True, text=True)
    result = str(result.stdout)
    label,line = result.split('pixel')
    x,y = re.findall("[-,+]?\d+\.\d+",line)
    return(x,y)

def xy2rd(x,y): # returns the RA & Dec equivalent to a camera pixel x,y
    result = subprocess.run(["wcs-xy2rd","-w",home_path+"/Solver/images/capture.wcs","-x",str(x),"-y",str(y)],capture_output=True, text=True)
    result = str(result.stdout)
    label,line = result.split('RA,Dec')
    ra,dec = re.findall("[-,+]?\d+\.\d+",line)
    return(float(ra),float(dec))

def pixel2dxdy(pix_x,pix_y): # converts a pixel position, into a delta angular offset from the image centre
    global value
    pix_scale = 3.74715 if value[4] == 'False' else 4*3.74715
    deg_x = (float(pix_x) - 640)*pix_scale/3600 # in degrees
    deg_y = (480-float(pix_y))*pix_scale/3600
    dxstr = "{: .1f}".format(float(60*deg_x)) # +ve if finder is left of Polaris
    dystr = "{: .1f}".format(float(60*deg_y)) # +ve if finder is looking below Polaris 
    return(deg_x,deg_y,dxstr,dystr)

def display(line0,line1,line2):
    global LCD_module,USB_module
    if LCD_module == True:
        lcd.clear()
        lcd.message = line0+'\n'+line1
    if USB_module == True:
        box.write(bytes(('0:'+line0+'\n').encode('UTF-8')))
        box.write(bytes(('1:'+line1+'\n').encode('UTF-8')))
        box.write(bytes(('2:'+line2+'\n').encode('UTF-8')))

def readNexus(): # Nexus USB port set to LX200 protocol
    global nexus_Pos, nexus_altaz, nexus_radec
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST,PORT))
        s.send(b':GR#')
        time.sleep(0.1)
        ra = str(s.recv(16).decode('ascii')).strip('#').split(':')
        s.send(b':GD#')
        time.sleep(0.1)
        dec = re.split(r'[:*]',str(s.recv(16).decode('ascii')).strip('#'))
    nexus_radec = (float(ra[0]) + float(ra[1])/60 + float(ra[2])/3600),(float(dec[0]) + float(dec[1])/60 + float(dec[2])/3600)
    nexus_altaz = convAltaz(*(nexus_radec))   
    print ('Nexus RA: ',hh2dms(nexus_radec[0]))
    print ('Nexus Dec: ',dd2dms(nexus_radec[1]))
    arr[0,1][0] = 'Nex: RA '+hh2dms(nexus_radec[0])
    arr[0,1][1] = '   Dec '+dd2dms(nexus_radec[1])

def zwoInit():
    global camera
    camera = asi.Camera(0)
    camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, camera.get_controls()['BandWidth']['MinValue'])
    camera.disable_dark_subtract()
    camera.set_control_value(asi.ASI_WB_B, 99)
    camera.set_control_value(asi.ASI_WB_R, 75)
    camera.set_control_value(asi.ASI_GAMMA, 50)
    camera.set_control_value(asi.ASI_BRIGHTNESS, 50)
    camera.set_control_value(asi.ASI_FLIP, 0)
    camera.set_image_type(asi.ASI_IMG_RAW8)

def zwoCapture(expTime,gain):
    global offset_flag,value
    camera.set_control_value(asi.ASI_GAIN, gain * 5)
    camera.set_control_value(asi.ASI_EXPOSURE, expTime * 1000000)# microseconds
    print(value[3],offset_flag)
    if value[3] == 'True':
        if offset_flag == False:
            copyfile(home_path+'/Solver/test.jpg',home_path+'/Solver/images/capture.jpg')
        else:
            copyfile(home_path+'/Solver/polaris.jpg',home_path+'/Solver/images/capture.jpg')
            print('using Polaris')
    else:
        camera.capture(filename=home_path+'/Solver/images/capture.jpg')

def imgDisplay(): #displays the captured image on the Pi desktop.
    for proc in psutil.process_iter():
        if proc.name() == "display":
            proc.kill() # delete any previous image display
    im = Image.open(home_path+'/Solver/images/capture.jpg')
    im.show()

def solveImage(): 
    global value, offset_flag, solve, scopeAlt, elapsed_time, solved_radec,solved_altaz
    scale = 4*3.75 if str(value[4]) == 'True' else 3.75
    scale_low = str(scale * 0.9)
    scale_high = str(scale * 1.1)
    display('Started solving','','')
    limitOptions = 		(["--no-plots",		# don't generate plots - this takes a ton of time
                            "--overwrite", 	# overwrite any existing files
                            "--skip-solved", 	# skip any files we've already solved
                            "--cpulimit","10"	# limit to 10 seconds(!). We use a fast timeout here because this code is supposed to be fast
                            ]) 
    optimizedOptions = 	(["--downsample","2",	# downsample 4x. 2 = faster by about 1.0 second; 4 = faster by 1.3 seconds
                            "--no-remove-lines",	# Saves ~1.25 sec. Don't bother trying to remove surious lines from the image
                            "--uniformize","0"	# Saves ~1.25 sec. Just process the image as-is
                            ])
    scaleOptions = 		(["--scale-units","arcsecperpix",	# next two params are in arcsecs. Supplying this saves ~0.5 sec
                            "--scale-low",scale_low,			# See config above
                            "--scale-high",scale_high			# See config above
                            ])
    fileOptions = 		(["--new-fits","none",	# Don't create a new fits
                            "--solved","none",	# Don't generate the solved output
                            "--match","none",		# Don't generate matched output
                            "--corr","none",		# Don't generate .corr files
                            "--rdls","none",		# Don't generate the point list
                            "--temp-axy"			# We can't specify not to create the axy list, but we can write it to /tmp
                            ])

    cmd = ["solve-field"]
    captureFile = home_path+"/Solver/images/capture.jpg"
    options = limitOptions + optimizedOptions + scaleOptions + fileOptions + [captureFile]
    start_time=time.time()
    # next line runs the plate-solve on the captured image file 
    if value[3] == 'False':
        result = subprocess.run(cmd + options, capture_output=True, text=True) 
    else:
        if offset_flag == False:
            copyfile(home_path+'/Solver/test.jpg',home_path+'/Solver/images/capture.jpg')
            result = subprocess.run(cmd + options, capture_output=True, text=True)         
        else:
            copyfile(home_path+'/Solver/polaris.jpg',home_path+'/Solver/images/capture.jpg')
            result = subprocess.run(cmd + options, capture_output=True, text=True) 
    elapsed_time = time.time() - start_time
    print ('solve elapsed time '+str(elapsed_time)[0:4]+' sec\n')
    print (result.stdout) # this line added to help debug.
    result = str(result.stdout)
    if ("solved" not in result):
        print('Bad Luck - Solve Failed')
        solve = False
        return
    solvedPos = applyOffset()
    ra,dec,d = solvedPos.radec(ts.now())
    solved_radec = ra.hours,dec.degrees
    solved_altaz = convAltaz(*(solved_radec))
    scopeAlt = solved_altaz[0]*math.pi/180
    arr[0,2][0] = 'Sol: RA '+hh2dms(solved_radec[0])
    arr[0,2][1] = '   Dec '+dd2dms(solved_radec[1])
    arr[0,2][2] = 'time: '+str(elapsed_time)[0:4]+' s'
    solve = True
    deltaCalc()

def applyOffset():
    global offset
    ra,dec = xy2rd(float(offset[0]),float(offset[1]))
    solved = Star(ra_hours=ra/15,dec_degrees=dec) # will set as J2000 as no epoch input
    solvedPos_scope = location.at(ts.now()).observe(solved) # now at Jnow and current location
    return(solvedPos_scope)

def deltaCalc():
    global offset,deltaAz,deltaAlt,elapsed_time
    deltaAz = solved_altaz[1] - nexus_altaz[1]
    if abs(deltaAz)>180:
        if deltaAz<0:
            deltaAz = deltaAz + 360
        else:
            deltaAz = deltaAz - 360
    deltaAz = 60*(deltaAz*math.cos(scopeAlt)) #actually this is delta'x' in arcminutes
    deltaAlt = solved_altaz[0] - nexus_altaz[0]
    deltaAlt = 60*(deltaAlt)  # in arcminutes
    deltaXstr = "{: .2f}".format(float(deltaAz))
    deltaYstr = "{: .2f}".format(float(deltaAlt))
    arr[0,3][0] = 'Delta: x= '+deltaXstr
    arr[0,3][1] = '       y= '+deltaYstr
    arr[0,3][2] = 'time: '+str(elapsed_time)[0:4]+' s'

def align():
    global align_count, solve, Lat
    readNexus()
    zwoCapture(value[1],value[2])
    imgDisplay()
    solveImage()
    if solve==False:
        return 
    align_ra = ':Sr'+dd2dms((solved_radec)[0])+'#'
    align_dec = ':Sd'+dd2aligndms((solved_radec)[1])+'#'
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST,PORT))
        s.send(bytes(align_ra.encode('ascii')))
        time.sleep(0.1)
        print(align_ra)
        if str(s.recv(1),'ascii') == '0':
            print('invalid position')
            return
        s.send(bytes(align_dec.encode('ascii')))
        time.sleep(0.1)
        print(align_dec)
        if str(s.recv(1),'ascii') == '0':
            print('invalid position')             
            return           
        s.send(b':CM#')
        time.sleep(0.1)
        print(':CM#')
        reply = str(s.recv(20),'ascii')
        print('reply: ',reply)
        s.send(b':GW#')
        time.sleep(0.1)
        p = str(s.recv(16),'ascii')
        print('Align status reply ',p)
        align_count +=1
        if p != 'AT2#':
            display('"select" aligns','align count: '+str(align_count),'Nexus reply: '+p[0:3])
        else:
            if p == 'AT2#':
                align_count = 0
                display('"select" syncs','Sync count '+str(align_count),'Nexus reports '+p[0:3])   
    return
    
def measure_offset():
    global offset, offset_str, offset_flag
    offset_flag = True
    display('started capture','','')
    zwoCapture(value[1],value[2])
    imgDisplay()
    solveImage()
    if solve == False:
        display('solve failed','','')
        return
    scope_x,scope_y = rd2xy(37.954,89.264136) # Polaris RA & Dec in J2000
    d_x,d_y,dxstr,dystr = pixel2dxdy(scope_x,scope_y) 
    offset = scope_x,scope_y
    offset_str = dxstr+','+dystr
    arr[0,5][1] = 'new '+offset_str
    arr[0,6][1] = 'new '+offset_str
    display(arr[0,5][0],arr[0,5][1],arr[0,5][2])
    save_config()
    offset_flag = False

def readNexusData(): # establishes Nexus is talking to us and get observer location and time data
    global location,Long,Lat
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST,PORT))
        display('looking for','Nexus','')
        s.send(b'#:P#')
        time.sleep(0.1)
        p = str(s.recv(15),'ascii')
        if p[0] == 'L': # means in low precision mode
            s.send(b'#:U#') # toggle to high precision
        display('Wifi link to','Nexus is open','')
        print('Wifi to Nexus open')
        s.send(b'#:Gt#')
        time.sleep(0.1)
        Lt = (str(s.recv(7),'ascii'))[0:6].split('*')
        Lat = float(Lt[0]+'.'+Lt[1])
        s.send(b':Gg#')
        time.sleep(0.1)
        Lg = (str(s.recv(8),'ascii'))[0:7].split('*')
        Long = -1*float(Lg[0]+'.'+Lg[1])
        location = earth+wgs84.latlon(Lat,Long)
        s.send(b':GL#')
        local_time = str(s.recv(16),'ascii').strip('#')
        s.send(b':GC#')
        local_date = str(s.recv(16),'ascii').strip('#')
        s.send(b':GG#')
        local_offset = float(str(s.recv(16),'ascii').strip('#'))
        print('Nexus reports: local datetime as',local_date, local_time, ' local offset:',local_offset)
        date_parts = local_date.split('/')
        local_date = date_parts[0]+'/'+date_parts[1]+'/20'+date_parts[2]
        dt_str = local_date+' '+local_time
        format  = "%m/%d/%Y %H:%M:%S"
        local_dt = datetime.strptime(dt_str, format)
        new_dt = local_dt + timedelta(hours = local_offset)
        print('Calculated UTC',new_dt)
        print('setting pi clock to:',end = " ")
        os.system('sudo date -u --set "%s"' % new_dt+'.000Z')
        s.send(b':GW#')
        time.sleep(0.1)
        p = str(s.recv(4),'ascii')
        if p != 'AT2#':
            display('Nexus reports','not aligned yet','')
        else:
            display('eFinder ready','Nexus reports'+p,'') 
        time.sleep(1)

def up_down(v):
    global x
    x = x + v
    display (arr[x,y][0],arr[x,y][1],arr[x,y][2])
    
def left_right(v):
    global y
    y = y + v
    display (arr[x,y][0],arr[x,y][1],arr[x,y][2])
    
def up_down_inc(i,sign):
    global value,increment
    arr[x,y][1] = int(arr[x,y][1])+increment[i]*sign
    value[i] = arr[x,y][1]
    display (arr[x,y][0],arr[x,y][1],arr[x,y][2])
    update_summary()
    time.sleep(0.1)
    
def flip(i):
    value[i] = not value[i]
    arr[x,y][1] = value[i]
    display (arr[x,y][0],arr[x,y][1],arr[x,y][2])
    update_summary()
    time.sleep(0.1)

def update_summary():
    global value
    arr[1,0][0] = 'Ex:'+str(value[1])+'  50:'+str(value[4])
    arr[1,0][1] = 'Gn:'+str(value[2])+' Test:'+str(value[3])
    save_config()

def go_solve():
    global x,y,solve
    readNexus()
    display('Image capture','','')
    zwoCapture(value[1],value[2])
    imgDisplay()
    display('Plate solving','','')
    solveImage()
    if solve == True:
        display('Solved','','')
    else:
        display('Not Solved','','')
    x=0
    y=3
    display(arr[0,3][0],arr[0,3][1],arr[0,3][2])

def goto():
    display('Attempting','GoTo++','')
    align()
    if solve == False:
        display('problem','solving','')
        return
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST,PORT))
        s.send(b':MS#')
        time.sleep(0.1)
        if str(s.recv(1),'ascii') != '0':
            print('GoTo problem')
            display('Problem with','GoTo++','')
        display('Performing',' GoTo++','')
    time.sleep(5) # replace with a check on goto progress
    go_solve()

def save_config():
    global offset, value
    with open(home_path+"/Solver/offset.config","w") as h:
        h.write(str(offset[0])+':'+str(offset[1])+':'+str(value[1])+':'+str(value[2])+':'+str(value[3])+':'+str(value[4])+'\n')

def get_config():
    global offset, value, offset_str
    if os.path.exists(home_path+"/Solver/offset.config") == False:
        return
    with open(home_path+"/Solver/offset.config") as h:
        for line in h:
            data = line.strip('\n').split(':')
            offset = float(data[0]),float(data[1])
            value = ['',int(data[2]),int(data[3]),(data[4]),(data[5])]
    d_x,d_y,dxstr,dystr = pixel2dxdy(offset[0],offset[1])
    offset_str = dxstr+','+dystr

def reset_offset():
    global offset
    offset = 640,480
    deg_x,deg_y,dxstr,dystr = pixel2dxdy(640,480)
    offset_str = dxstr+','+dystr
    arr[0,5][1] = 'new '+offset_str
    arr[0,6][1] = 'new '+offset_str
    display(arr[x,y][0],arr[x,y][1],arr[x,y][2])
    save_config()

def reader():
    global button
    while True:
        if box in select.select([box], [], [], 0)[0]:
            button = box.readline().decode('ascii').strip('\r\n')
        time.sleep(0.1)

#main code starts here
if os.path.exists(home_path+"/Solver/eFinder.config") == True:
    with open(home_path+"/Solver/eFinder.config") as h:
        for line in h:
            if(line.startswith("azSpeed")):
                label,data = line.split(':')
                azSpeed = float(data)
            elif(line.startswith("altSpeed")):
                label,data = line.split(':')
                altSpeed = float(data)    


try:
    import board
    import busio
    import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd
    i2c = busio.I2C(board.SCL, board.SDA)
    lcd = character_lcd.Character_LCD_RGB_I2C(i2c, 16, 2)
    lcd.color = [100, 0, 0]
    LCD_module = True
    time.sleep(2)
except Exception as ex:
    print('no LCD setup',ex)
    LCD_module = False

try:
    box = serial.Serial( '/dev/ttyACM0',
                     baudrate = 115200,
                     stopbits = serial.STOPBITS_ONE,
                     bytesize = serial.EIGHTBITS,
                     writeTimeout = 0,
                     timeout = 0,
                     rtscts = False,
                     dsrdtr = False )
    box.write(b'0:ScopeDog eFinder\n')
    box.write(b'1:eFinder found   \n')
    box.write(b'2:                \n')
    USB_module = True
except Exception as ex:
    USB_module = False

display('ScopeDog','eFinder v'+version,'')
print('LCD:',LCD_module,'  USB:',USB_module)

x = y = 0 # x, y  define what page the display is showing
deltaAz = deltaAlt = 0
label = ['','Exposure sec.','Camera Gain','Test Mode','50mm Finder']
value = [0,1,25,True,False]
increment = [0,1,5,1,1]
offset_flag = False
align_count = 0
offset = 640,480
solve = False
#time.sleep(1)

planets = load('de421.bsp')
earth = planets['earth']
ts = load.timescale()

readNexusData()

get_config()
display('ScopeDog eFinder','Ready','')
# array determines what is displayed, computed and what each button does for each screen.
# [first line,second line,third line, up button action,down...,left...,right...,select button short press action, long press action]
# empty string does nothing.
# example: left_right(-1) allows left button to scroll to the next left screen
# button texts are infact def functions
p=""
home =      [   'ScopeDog',
                'eFinder',
                'ver'+version,
                '',
                'up_down(1)',  
                '',
                'left_right(1)',
                'go_solve()',
                '']
nex =       [   'Nex: RA ',
                '    Dec ',
                '',
                '',
                '',
                'left_right(-1)',
                'left_right(1)',
                'go_solve()',
                'goto()']
sol =       [   'No solution yet',
                '"select" solves',
                '',
                '',
                '',
                'left_right(-1)',
                'left_right(1)',
                'go_solve()',
                'goto()']
delta =     [   'Delta: No solve',
                '"select" solves',
                '',
                '',
                '',
                'left_right(-1)',
                'left_right(1)',
                'go_solve()',
                'goto()']
aligns =     [   'Select aligns',
                'not aligned yet',
                str(p),
                '',
                '',
                'left_right(-1)',
                'left_right(1)',
                'align()',
                '']
polar =     [   '"Select" Polaris',
                offset_str,
                '',
                '',
                '',
                'left_right(-1)',
                'left_right(1)',
                'measure_offset()',
                '']
reset =     [   'Select Resets',
                offset_str,
                '',
                '',
                '',
                'left_right(-1)',
                '',
                'reset_offset()',
                '']
summary =   [   '',
                '',
                '',
                'up_down(-1)',
                '',
                '',
                'left_right(1)',
                'go_solve()',
                '']
exp =       [   'Exposure sec.',
                value[1],
                '',
                'up_down_inc(1,1)',
                'up_down_inc(1,-1)',
                'left_right(-1)',
                'left_right(1)',
                'go_solve()',
                'goto()']
gn =        [   'Gain.',
                value[2],
                '',
                'up_down_inc(2,1)',
                'up_down_inc(2,-1)',
                'left_right(-1)',
                'left_right(1)',
                'go_solve()',
                'goto()']
mode =      [   'Test mode',
                value[3],
                '',
                'flip(3)',
                'flip(3)',
                'left_right(-1)',
                'left_right(1)',
                'go_solve()',
                'goto()']
finder =    [   '50mm Finder',
                value[4],
                '',
                'flip(4)',
                'flip(4)',
                'left_right(-1)',
                '',
                'go_solve()',
                'goto()']


arr = np.array([[home,nex,sol,delta,aligns,polar,reset],[summary,exp,gn,mode,finder,finder,finder]])
update_summary()
deg_x,deg_y,dxstr,dystr = pixel2dxdy(offset[0],offset[1])
offset_str = dxstr+','+dystr
readNexus()

#find a camera
asi.init("/lib/zwoasi/armv7/libASICamera2.so")
num_cameras = asi.get_num_cameras()
if num_cameras == 0:   
    display('Error:','   no camera found','')
    exit()
else:
    cameras_found = asi.list_cameras()
    camera_id = 0
    zwoInit()  
    display('ZWO camera found','','')
    print('camera found')
    time.sleep(1)

display('ScopeDog eFinder','v'+version,'')
button = ""
if USB_module == True:
    scan = threading.Thread(target=reader)
    scan.start()

# main program loop, scan buttons and refresh lcd display

while True:    #next loop reads all buttons and sets display option x,y
    if LCD_module == True:
        if lcd.select_button:
            while True:
                time.sleep(0.3)
                if lcd.select_button == False: # catch a short button <0.3 sec press,
                    exec(arr[x,y][7])
                    break
                time.sleep(1)
                if lcd.select_button == False: # catch a longerbutton press, <0.3 sec
                    exec(arr[x,y][8])
                    break
        elif lcd.down_button:
            exec(arr[x,y][4])
        elif lcd.up_button:
            exec(arr[x,y][3])
        elif lcd.left_button:
            exec(arr[x,y][5])
        elif lcd.right_button:
            exec(arr[x,y][6])
    if USB_module == True:
        if button == '21':
            exec(arr[x,y][7])
        elif button == '20':
            exec(arr[x,y][8])
        elif button =='19':
            exec(arr[x,y][4])
        elif button=='17':
            exec(arr[x,y][3])
        elif button == '16':
            exec(arr[x,y][5])
        elif button == '18':
            exec(arr[x,y][6])
        button=''
    time.sleep(0.1)
