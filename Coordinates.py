import math
from skyfield.api import load, Star, wgs84

class Coordinates:
    def __init__(self) -> None:
        self.planets = load('de421.bsp')
        self.earth = self.planets['earth']
        self.ts = load.timescale()

    def conv_altaz(self, nexus, ra, dec): # decimal ra in hours, decimal dec.
        Rad = math.pi/180
        t = self.ts.now()
        LST = t.gmst + nexus.get_long()/15 #as decimal hours
        ra =ra * 15 # need to work in degrees now
        LSTd = LST * 15
        LHA = (LSTd - ra + 360) - ((int)((LSTd - ra + 360)/360))*360
        x = math.cos(LHA * Rad) * math.cos(dec * Rad)
        y = math.sin(LHA * Rad) * math.cos(dec * Rad)
        z = math.sin(dec * Rad)
        xhor = x * math.cos((90 - nexus.get_lat()) * Rad) - z * math.sin((90 - nexus.get_lat()) * Rad)
        yhor = y
        zhor = x * math.sin((90 - nexus.get_lat()) * Rad) + z * math.cos((90 - nexus.get_lat()) * Rad)
        az = math.atan2(yhor, xhor) * (180/math.pi) + 180
        alt = math.asin(zhor) * (180/math.pi)
        return(alt,az)

    def dd2dms(self, dd):
        is_positive = dd >= 0
        dd = abs(dd)
        minutes,seconds = divmod(dd*3600,60)
        degrees,minutes = divmod(minutes,60)
        sign = '+' if is_positive else '-'
        dms = '%s%02d:%02d:%02d' % (sign,degrees,minutes,seconds)
        return(dms)

    def dd2aligndms(self, dd):
        is_positive = dd >= 0
        dd = abs(dd)
        minutes,seconds = divmod(dd*3600,60)
        degrees,minutes = divmod(minutes,60)
        sign = '+' if is_positive else '-'
        dms = '%s%02d*%02d:%02d' % (sign,degrees,minutes,seconds)
        return(dms)

    def ddd2dms(self, dd):
        minutes,seconds = divmod(dd*3600,60)
        degrees,minutes = divmod(minutes,60)
        dms = '%03d:%02d:%02d' % (degrees,minutes,seconds)
        return(dms)

    def hh2dms(self, dd):
        minutes,seconds = divmod(dd*3600,60)
        degrees,minutes = divmod(minutes,60)
        dms = '%02d:%02d:%02d' % (degrees,minutes,seconds)
        return(dms)

    def get_ts(self):
        return self.ts

    def get_earth(self):
        return self.earth