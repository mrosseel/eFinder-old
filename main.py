from machine import Pin,SPI
import framebuf
import time
import sys
import select

DC = 8
RST = 12
MOSI = 11
SCK = 10
CS = 9
ln = ["ScopeDog eFinder","","No host yet"]

class OLED_2inch23(framebuf.FrameBuffer):
    def __init__(self):
        self.width = 128
        self.height = 32
        
        self.cs = Pin(CS,Pin.OUT)
        self.rst = Pin(RST,Pin.OUT)
        
        self.cs(1)
        self.spi = SPI(1)
        self.spi = SPI(1,1000_000)
        self.spi = SPI(1,10000_000,polarity=0, phase=0,sck=Pin(SCK),mosi=Pin(MOSI),miso=None)
        self.dc = Pin(DC,Pin.OUT)
        self.dc(1)
        self.buffer = bytearray(self.height * self.width // 8)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()
        
        self.white =   0xffff
        self.balck =   0x0000
        
    def write_cmd(self, cmd):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([buf]))
        self.cs(1)

    def init_display(self):
        self.rst(1)
        time.sleep(0.001)
        self.rst(0)
        time.sleep(0.01)
        self.rst(1)
        self.write_cmd(0xAE)# turn off OLED display
        self.write_cmd(0x04)# set lower column address
        self.write_cmd(0x10)# set higher column address
        self.write_cmd(0x40)# set Display Start Line
        self.write_cmd(0x81)# set Contrast Control - 1st byte
        self.write_cmd(116)# set Contrast Control - 2nd byte - value
        #self.write_cmd(0x80)# reset contrast and brightness
        #self.write_cmd(0x82)# set Brightness Control - 1st byte
        #self.write_cmd(0x01)# set Brightness Control - 2nd byte - value
        self.write_cmd(0xA1)# set segment re-map
        self.write_cmd(0xA6)# Set normal display (reset) 
        self.write_cmd(0xA8)# Set Mux ratio - byte 1
        self.write_cmd(0x1F)# byte 2   
        self.write_cmd(0xC8)# Scan Direction - remapped mode  
        self.write_cmd(0xD3)# set display offset byte 1
        self.write_cmd(0x00)# display offset byte 2
        self.write_cmd(0xD5)# set Display Clock divide ratio - byte 1 
        self.write_cmd(0xF0)# byte 2
        self.write_cmd(0xD8)# set area colour mode - byte 1
        self.write_cmd(0x05)# byte 2 (low power mode)
        self.write_cmd(0xD9)# set pre-charge period - byte 1
        self.write_cmd(0xC2)# Set Pre-Charge as 15 Clocks & Discharge as 1 Clock
        self.write_cmd(0xDA)# set com pins hardware configuration - byte 1
        self.write_cmd(0x12)# byte 2
        self.write_cmd(0xDB)# set vcomh - byte 1
        self.write_cmd(0x08)# Set VCOM Deselect Level - byte 2
        self.write_cmd(0xAF); # turn on display

    def show(self):
        for page in range(0,4):
            self.write_cmd(0xb0 + page)
            self.write_cmd(0x04)
            self.write_cmd(0x10)
            self.dc(1)
            for num in range(0,128):
                self.write_data(self.buffer[page*128+num])

def send_pin(p):
    n=0
    for n in range(5):
        if p.value()== True: 
            return
    time.sleep(0.3)
    if p.value()==True:
        print(str(p)[4:6])
        if str(p)[4:6] == '16' and ln[2][0:6] == 'Bright':
            f=open('bright.txt','w')
            f.write(str(contrast))
            f.close()
    elif str(p)[4:6]=='21':
        print("20\n")
    time.sleep(0.1)

def adj_brightness(p):
    global contrast
    n=0
    for n in range(4):
        if p.value()== True: 
            return
    time.sleep(0.3)
    if p.value()==True:
        if str(p)[4:6]== '17': #up
            if contrast < 239:
                contrast = contrast +16
        elif str(p)[4:6]== '19': #down
            if contrast > 16:
                contrast = contrast - 16 
        ln[2] = 'Brightness '+str(contrast)
        OLED.write_cmd(0x81)# set Contrast Control - 1st byte
        OLED.write_cmd(contrast)# set Contrast Control - 2nd byte - value
        OLED.fill(0x0000) 
        OLED.text(ln[0],1,1,OLED.white)
        OLED.text(ln[1],1,12,OLED.white)
        OLED.text(ln[2],1,23,OLED.white)
        OLED.show()

        
if __name__=='__main__':

    OLED = OLED_2inch23()
    OLED.fill(0x0000) 
    OLED.text(ln[0],1,1,OLED.white)
    OLED.text(ln[1],1,12,OLED.white)
    OLED.text(ln[2],1,23,OLED.white)
    OLED.show()
    left = Pin(16,Pin.IN,Pin.PULL_UP)
    up = Pin(17,Pin.IN,Pin.PULL_UP)
    right = Pin(18,Pin.IN,Pin.PULL_UP)
    down = Pin(19,Pin.IN,Pin.PULL_UP)
    select_button = Pin(21,Pin.IN,Pin.PULL_UP)
    left.irq(trigger=Pin.IRQ_FALLING, handler=send_pin)
    up.irq(trigger=Pin.IRQ_FALLING, handler=send_pin)
    right.irq(trigger=Pin.IRQ_FALLING, handler=send_pin)
    down.irq(trigger=Pin.IRQ_FALLING, handler=send_pin)
    select_button.irq(trigger=Pin.IRQ_FALLING, handler=send_pin)
    count =0
    try:
        f=open('bright.txt')
        contrast = int(float(f.read()))
        f.close()
    except:
        f=open('bright.txt','w')
        f.write('114')
        f.close()
        contrast = 114
        
    while True:
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            ch = sys.stdin.readline().strip('\n')
            y = int(ch[0:1])
            ln[y] = ch[2:]
            OLED.fill(0x0000) 
            OLED.text(ln[0],1,1,OLED.white)
            OLED.text(ln[1],1,12,OLED.white)
            if ln[2] == 'Brightness':
                ln[2] = 'Brightness '+str(contrast)
                up.irq(trigger=Pin.IRQ_FALLING, handler=adj_brightness)
                down.irq(trigger=Pin.IRQ_FALLING, handler=adj_brightness)
            else:
                up.irq(trigger=Pin.IRQ_FALLING, handler=send_pin)
                down.irq(trigger=Pin.IRQ_FALLING, handler=send_pin)
            OLED.text(ln[2],1,23,OLED.white)
            OLED.show()
