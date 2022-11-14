# ScopeDog eFinder

- [ScopeDog eFinder](#scopedog-efinder)
  - [Source code](#source-code)
  - [Needed parts](#needed-parts)
    - [Purchase of the hardware](#purchase-of-the-hardware)
  - [Nexus DSC Pro](#nexus-dsc-pro)
    - [Update of the Nexus DSC Pro firmware](#update-of-the-nexus-dsc-pro-firmware)
    - [Network settings on the Nexus DSC Pro](#network-settings-on-the-nexus-dsc-pro)
  - [Software](#software)
    - [Raspberry Pi 4](#raspberry-pi-4)
      - [Install OS and needed dependencies](#install-os-and-needed-dependencies)
      - [Install astrometry.net](#install-astrometrynet)
      - [Install the ZWO ASI Linux SDK](#install-the-zwo-asi-linux-sdk)
      - [Start eFinder automatically after boot](#start-efinder-automatically-after-boot)
      - [Install RTL8192EU driver for the TP-LINK TL-WN823N](#install-rtl8192eu-driver-for-the-tp-link-tl-wn823n)
    - [The Raspberry Pi Pico handbox](#the-raspberry-pi-pico-handbox)
    - [Changelog](#changelog)
  - [Hardware](#hardware)
    - [Adding the OLED display to the Raspberry Pi Pico](#adding-the-oled-display-to-the-raspberry-pi-pico)
    - [Adding the little joystick to the Raspberry Pi Pico](#adding-the-little-joystick-to-the-raspberry-pi-pico)
    - [Insert the Raspberry Pi Pico in a nice box](#insert-the-raspberry-pi-pico-in-a-nice-box)
    - [Mounting the eFinder on the telescope](#mounting-the-efinder-on-the-telescope)
  - [Testing the eFinder](#testing-the-efinder)
    - [Testing the eFinder outside](#testing-the-efinder-outside)
    - [Connect to the Nexus DSC wifi](#connect-to-the-nexus-dsc-wifi)
    - [How to work with the handpad](#how-to-work-with-the-handpad)
      - [In the VNC GUI version](#in-the-vnc-gui-version)
      - [In the handpad version](#in-the-handpad-version)

## Source code

- The source code can be found at [google drive](https://drive.google.com/drive/folders/1GnNv5xhHqUr66mJKaSsVWqEgyuoLcbI8).

## Needed parts

### Purchase of the hardware

As I live in Belgium, this section is very Europe-centric.  I ordered the ASI camera at Teleskop Service (Germany) and the rest in the Netherlands.

| Ordered    | Product                                                                                                                                                                                    | Company           | Amount   | Arrival   |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------- | -------- | ---------- |
| 03/08/2022 | Software                                                                                                                                                                                   | Keith Venables    | 26.98 €  | 03/08/2022 |
| 03/08/2022 | [ASI120MM-S](https://www.teleskop-express.de/shop/product_info.php/info/p7109)                                                                                                             | Teleskop Service  | 248.51 € | 11/08/2022           |
| 03/08/2022 | [Raspberry Pi 4 model B - 4GB](https://www.raspberrystore.nl/PrestaShop/nl/raspberry-pi-v4/228-raspberry-pi-4b4gb-765756931182.html?search_query=Raspberry+Pi+4+model+B+-+4GB&results=203) | Raspberrystore.nl | 74.95 €  | 10/08/2022           |
| 03/08/2022 | [Raspberry Pi Pico](https://www.raspberrystore.nl/PrestaShop/nl/raspberry-pi-pico/312-raspberry-pi-pico-0617588405587.html?search_query=Raspberry+Pi+4+Pico&results=203)                   | Raspberrystore.nl | 3.99 €   | 10/08/2022           |
| 03/08/2022 | [2 x 1x40 header](https://www.raspberrystore.nl/PrestaShop/nl/raspberry-pi-pico/320-soldeerpennen-1x40-voor-de-raspberry-pi-pico.html?search_query=1x40+header&results=44)                 | Raspberrystore.nl | 2.00 €   | 10/08/2022           |
| 03/08/2022 | Verzendkosten Astroberrystore.nl                                                                                                                                                           | Raspberrystore.nl | 12.74 €  | 10/08/2022           |
| 03/08/2022 | [2.23 OLED Display Module for Raspberry Pi Pico](https://www.amazon.nl/gp/product/B093SYSX5S/ref=ppx_od_dt_b_asin_title_s00?ie=UTF8&psc=1)                                                 | Amazon (.nl)      | 20.99 €  | 09/08/2022          |
| 03/08/2022 | [Geekworm Raspberry Pi 4 Aluminum Case](https://www.amazon.nl/gp/product/B07ZVJDRF3/ref=ppx_od_dt_b_asin_title_s01?ie=UTF8&psc=1)                                                          | Amazon (.nl)      | 14.89 €  | 08/08/2022           |
| 03/08/2022 | [Sandisk Ultra 32 GB microSDHC](https://www.amazon.nl/gp/product/B08GY9NYRM/ref=ppx_od_dt_b_asin_title_s02?ie=UTF8&psc=1)                                                                  | Amazon (.nl)      | 8.01 €   | 08/08/2022           |
| 03/08/2022 | [100 x 60 x 25 mm DIY box](https://www.amazon.nl/gp/product/B07V2Q32H8/ref=ppx_od_dt_b_asin_title_s02?ie=UTF8&psc=1)                                                                       | Amazon (.nl)      | 10.62 €  | 08/08/2022           |
| 03/08/2022 | [Lon0167  Momentary Circuit Control Tactile Tact Push Button Switch](https://www.amazon.nl/gp/product/B0842JYXC8/ref=ppx_yo_dt_b_asin_title_o00_s00?ie=UTF8&psc=1)                         | Amazon (.nl)      | 11.31 €  | 16/08/2022           |
| 03/08/2022 | [50 mm F1.8 CCTV-lens for C-mount](https://www.amazon.nl/gp/product/B08BF7DRXR/ref=ppx_yo_dt_b_asin_title_o02_s00?ie=UTF8&psc=1)                                                           | Amazon (.nl)      | 48.38 €  | 16/08/2022           |
| 10/10/2022 | [TP-Link 300 Mbps Wifi USB-adapter (TL-WN823N)](https://www.amazon.nl/dp/B0088TKTY2/ref=pe_28126711_487805961_TE_item)                                                                     | Amazon (.nl)      | 9.95 €  | 11/10/2022           |
|Total      |                                                                                                                                                                                            |                   | 493.32 € |            |

## Nexus DSC Pro

### Update of the Nexus DSC Pro firmware

- Remove the micro SD card from the Nexus DSC Pro.
- Insert the micro SD card into a card reader of your computer.
- Copy the firmware image (nxpro.fw) from the google drive to the micro SD card.  This is a not yet released version (1.1.17, the latest version on the website is 1.0.2).  At least version 1.1.17 is needed.
- Make sure you properly eject the micro SD card from your computer.
- Insert the micro SD card back into the slot of the Nexus DSC Pro.
- Press and hold the OK button and turn the Nexus DSC Pro.
- A screen is shown asking if it is OK to update the firmware.  Press OK and wait till the update is completed.
- In the info menu, the correct version of the firmware should be shown (1.1.16).

### Network settings on the Nexus DSC Pro

Make sure the following settings are set on the Network page:

- WiFi Mode: Access Point
- DHCP: Disabled
- SSID: Name the network
- Password: Select a password or leave blank
- Channel: 6 (The channel needs to be 6 to be able to connect the eFinder, a VNC client, and SkySafari on a tablet)
- Protocol: LX200 (ServoCAT will not connect with the eFinder)

## Software

### Raspberry Pi 4

#### Install OS and needed dependencies

- Download the [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
- Install the standard 32bit Raspberry Pi OS.
- Enter *efinder* as username, *efinder* as password.
- Install applications

```bash
# For remote Finder access from a Mac
sudo apt install netatalk

sudo apt install libatlas3-base libbz2-dev libcairo2-dev libnetpbm10-dev netpbm libpng-dev libjpeg-dev zlib1g-dev swig libcfitsio-dev imagemagick python3-pil.imagetk

# Install the needed python libraries
pip install numpy==1.23.1
pip install fitsio
pip install astropy
pip install pyfits
pip install Skyfield
```

- Configure netatalk.  Using netatalk, you can select *Network* in the macOS Finder and select *raspberry* to see the contents of the /home directory of the Raspberry Pi on your Mac. Make sure the */etc/netatalk/afp.conf* configuration file is as follows:

```bash
[Homes]
 basedir regex = /home
```

- Restart netatalk:

```bash
sudo systemctl restart netatalk
```

- Edit */etc/profile*. Add the following line to the end of the file:

```bash
export PATH=/home/efinder/.local/bin:/usr/local/astrometry/bin:$PATH
```

- Remove the need for password during code execution:

```bash
sudo visudo
```

- Add the following line to the end:

```bash
efinder ALL = NOPASSWD: /bin/date, /sbin/reboot
```

- Add the needed folders for the eFinder software.

```bash
mkdir ~/Solver
mkdir ~/Solver/images/
mkdir ~/Solver/Stills/
```

- Checkout the eFinder software from GitHub

```bash
cd ~
git clone git@github.com:WimDeMeester/eFinder.git Solver
```

- Reboot

#### Install astrometry.net

- Download the latest version (0.91) of astrometry.net from [GitHub](https://github.com/dstndstn/astrometry.net/releases/tag/0.91).
- Unpack the tar.gz file

```bash
tar zxvf astrometry.net-0.91.tar.gz
```

- Build astrometry.net

```bash
cd astrometry.net-0.91
sudo make
sudo make py
sudo make extra
sudo make install
```

- Copy some index and catalog files:

```bash
sudo cp /home/efinder/Downloads/ver\ 11\ non-astroberry\ Raspian\ build/Indices/index-41* /usr/local/astrometry/data/
sudo cp -r /home/efinder/Downloads/ver\ 11\ non-astroberry\ Raspian\ build/annotate_data/ /usr/local/astrometry/
```

#### Install the ZWO ASI Linux SDK

- Download the SDK from the Developer tab of the [driver page](https://astronomy-imaging-camera.com/software-drivers).
- Unpack the SDK:

```bash
bunzip2 ASI_linux_mac_SDK_V1.26.tar.bz2
tar xvf ASI_linux_mac_SDK_V1.26.tar
cd ASI_linux_mac_SDK_V1.26/lib/
sudo mkdir /lib/zwoasi
sudo cp -r * /lib/zwoasi/
sudo install asi.rules /lib/udev/rules.d
pip3 install zwoasi
```

#### Start eFinder automatically after boot

- Find the PATH

```bash
echo $PATH
```

- Adapt crontab:

```bash
crontab -e
```

- Add the PATH and the DISPLAY variable to the crontab

```bash
export PATH=<The returned path from the echo $PATH command>
DISPLAY=:0
```

- Add the following line to start up the eFinder code automatically:

```bash
@reboot sleep 20 && (cd /home/efinder/Solver ; /usr/bin/python /home/efinder/Solver/eFinderVNCGUI_wifi.py >> /home/efinder/logs.txt 2>&1)
```

#### Install RTL8192EU driver for the TP-LINK TL-WN823N

- Install the needed packages

```bash
sudo apt-get install git raspberrypi-kernel-headers build-essential dkms
```

- Clone the driver from the GitHub repository

```bash
git clone https://github.com/Mange/rtl8192eu-linux-driver
cd rtl8192eu-linux-driver
```

- Make sure the following lines are in the ***Makefile***:

```bash
CONFIG_PLATFORM_I386_PC = n
CONFIG_PLATFORM_ARM_RPI = y
```

- Add and install the driver to DKMS

```bash
sudo dkms add .
sudo dkms install rtl8192eu/1.0
```

- Make sure the driver is loaded correctly

```bash
echo "blacklist rtl8xxxu" | sudo tee /etc/modprobe.d/rtl8xxxu.conf
echo -e "8192eu\n\nloop" | sudo tee /etc/modules
```

- Fix possible plugging/replugging issue and sforce the driver to be active from boot:

```bash
echo -e "8192eu\n\nloop" | sudo tee /etc/modules
echo "options 8192eu rtw_power_mgnt=0 rtw_enusbss=0" | sudo tee /etc/modprobe.d/8192eu.conf;
```

- Reboot the system

```bash
sudo reboot
```

- Configure the new Wifi network
- Disable the Wifi card from the Raspberry Pi by adding the following lines to ***/etc/modprobe.d/raspi-blacklist.conf***

```bash
blacklist brcmfmac
blacklist brcmutil
```

- Reboot the system

```bash
sudo reboot
```

### The Raspberry Pi Pico handbox

The software for the Raspberry Pi Pico handbox is written in micropython.  We first need to install micropython on the board.

- Download *Thonny* from the [website](https://thonny.org/).
- Connect the Raspberry Pi Pico to your computer, while pushing the reset button.
- Start *Thonny* and select to install micropython (at the bottom right).
- The Raspberry Pi Pico will automatically reboot and install micropython.
- After the Raspberry Pi Pico was restarted, open **main.py** in Thonny and select **Save As...**.  Select the Raspberry Pi Pico and save the file as **main.py**.  The screen of the handbox should show *ScopeDog eFinder - No eFinder yet*.

### Changelog

The changelog of the software can be found [here](CHANGELOG.md).

## Hardware

### Adding the OLED display to the Raspberry Pi Pico

- Solder the header to the Raspberry Pi Pico.  Check if you are soldering the header to the correct side of the Raspberry Pi Pico (I soldered it the wrong side first).
- Make sure to also solder a cable to GP16, GP17, GND, GP18, GP19, and GP21.
- Push the OLED display on the soldered header.
- ADD PICTURES!!!

### Adding the little joystick to the Raspberry Pi Pico

### Insert the Raspberry Pi Pico in a nice box

### Mounting the eFinder on the telescope

## Testing the eFinder

- For the images that are in the repository (polaris and M 13), set to 200mm.

### Testing the eFinder outside

### Connect to the Nexus DSC wifi

- Set up the Pi wifi to ‘know’ the Nexus DSC wifi DSC & password. That way on Pi boot it will always look for the Nexus wifi and connect as a priority.

### How to work with the handpad

#### In the VNC GUI version

- Simple press: Capture/solve & display RA, Dec & deltas.
- Up: Nexus align or Local Sync
- Down: Goto++

#### In the handpad version

![image](doc/menu.png)


## Development environment

*[Install poetry][https://python-poetry.org/docs/#installation] to manage the python dependencies.*

Install the dependencies and the virtual environment (do this once):

`poetry install`

Activate a python virtual environment (do this every time):

`poetry shell`
