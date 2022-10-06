import serial
import time
import socket
from skyfield.api import load, Star, wgs84
from datetime import datetime, timedelta
import os
import math
import re

class Nexus:
    def __init__(self, handpad, coordinates) -> None:
        self.handpad = handpad
        self.aligned = False
        self.nexus_link = 'none'
        self.coordinates = coordinates
        self.NexStr = 'not connected'

        try:
            self.ser = serial.Serial("/dev/ttyS0",baudrate=9600)
            self.ser.write(b':P#')
            time.sleep(0.1)
            p = str(self.ser.read(self.ser.in_waiting),'ascii')
            if p[0] == 'L':
                self.ser.write(b':U#')
            self.ser.write(b':P#')
            time.sleep(0.1)
            print ('Connected to Nexus in',str(self.ser.read(self.ser.in_waiting),'ascii'),'via USB')
            self.NexStr = 'connected'
            self.handpad.display('Found Nexus','via USB','')
            time.sleep(1)
            self.nexus_link = 'USB'
        except:
            self.HOST = '10.0.0.1'
            self.PORT = 4060
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    s.connect((self.HOST,self.PORT))
                    s.send(b':P#')
                    time.sleep(0.1)
                    p = str(s.recv(15),'ascii')
                    if p[0] == 'L':
                        s.send(b':U#')
                    s.send(b':P#')
                    time.sleep(0.1)
                    print ('Connected to Nexus in',str(s.recv(15),'ascii'),'via wifi')
                    self.NexStr = 'connected'
                    self.handpad.display('Found Nexus','via WiFi','')
                    time.sleep(1)
                    self.nexus_link = 'Wifi'
            except:
                print('no USB or Wifi link to Nexus')
                self.handpad.display('Nexus not found','','')

    def write(self, txt):
        #print('write',flag)
        if self.nexus_link == 'USB':
            self.ser.write(bytes(txt.encode('ascii')))
        else:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.HOST,self.PORT))
                s.send(bytes(txt.encode('ascii')))
        print('sent',txt,'to Nexus')

    def get(self, txt):
        if self.nexus_link == 'USB':
            self.ser.write(bytes(txt.encode('ascii')))
            time.sleep(0.1)
            res = str(self.ser.read(self.ser.in_waiting).decode('ascii')).strip('#')
        else:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.HOST,self.PORT))
                s.send(bytes(txt.encode('ascii')))
                time.sleep(0.1)
                res = str(s.recv(16).decode('ascii')).strip('#')
        print('sent',txt,'got',res,'from Nexus')
        return (res)

    def read(self): # establishes Nexus is talking to us and get observer location and time data
        Lt = self.get(':Gt#')[0:6].split('*')
        self.lat = float(Lt[0]+'.'+Lt[1])
        Lg = self.get(':Gg#')[0:7].split('*')
        self.long = -1*float(Lg[0] + '.' + Lg[1])
        self.location = self.coordinates.get_earth() + wgs84.latlon(self.lat,self.long)
        local_time = self.get(':GL#')
        local_date = self.get(':GC#')
        local_offset = float(self.get(':GG#'))
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
        p = self.get(':GW#')
        if p != 'AT2#':
            self.handpad.display('Nexus reports','not aligned yet','')
        else:
            self.handpad.display('eFinder ready','Nexus reports'+p,'')
            self.aligned = True
        time.sleep(1)

    # Was readNexus
    def read_altAz(self, arr): # Nexus USB port set to LX200 protocol
        ra = self.get(':GR#').split(':')
        dec = re.split(r'[:*]',self.get(':GD#'))
        self.radec = (float(ra[0]) + float(ra[1])/60 + float(ra[2])/3600),math.copysign(abs(float(dec[0]) + float(dec[1])/60 + float(dec[2])/3600),float(dec[0]))
        self.altaz = self.coordinates.conv_altaz(self, *(self.radec))
        self.scope_alt = self.altaz[0]*math.pi/180
        print ('Nexus RA:  ', self.coordinates.hh2dms(self.radec[0]),'  Dec: ', self.coordinates.dd2dms(self.radec[1]))
        if (arr is not None):
            arr[0,1][0] = 'Nex: RA ' + self.coordinates.hh2dms(self.radec[0])
            arr[0,1][1] = '   Dec ' + self.coordinates.dd2dms(self.radec[1])
        p = self.get(':GW#')
        if p == 'AT2#':
            if (arr is not None):
                arr[0,4][1] = 'Nexus is aligned'
                arr[0,4][0] = "'Select' syncs"

        if (arr is not None):
            return arr

    def get_location(self):
        return self.location

    def get_long(self):
        return self.long

    def get_lat(self):
        return self.lat

    def get_scope_alt(self):
        return self.scope_alt

    def get_altAz(self):
        return self.altaz

    def get_radec(self):
        return self.radec

    def get_nexus_link(self):
        return self.nexus_link

    def get_nex_str(self):
        return self.NexStr

    def is_aligned(self):
        return self.aligned

    def set_aligned(self, aligned):
        self.aligned = aligned

    def set_scope_alt(self, scope_alt):
        self.scope_alt = scope_alt
