#!/bin/sh
HOME=/home/efinder
apt-get update && apt -y upgrade
apt-get install -y netatalk
echo '[Homes]' >> /etc/netatalk/afp.conf
echo 'basedir regex = /home' >> /etc/netatalk/afp.conf
systemctl restart netatalk
apt-get install -y python3-dev python3-tk gcc cargo rustc libssl-dev # needed for poetry install
apt-get install -y libatlas-base-dev # needed for astropy compile
apt-get install -y make automake g++ wcslib-dev wcstools # needed for astrometry.net compile
apt-get install -y git pip neovim wget patch # patch is needed to compile fitsio
apt install -y libcairo2-dev libnetpbm10-dev netpbm libpng-dev libjpeg-dev zlib1g-dev libbz2-dev swig libcfitsio-dev
cd $HOME
sudo -u efinder git clone https://github.com/dstndstn/astrometry.net.git
sudo -u efinder python3 -m pip install --upgrade pip
sudo -u efinder -- curl -sSL https://install.python-poetry.org | CARGO_NET_GIT_FETCH_WITH_CLI=true python3 -
echo 'export PATH="/home/efinder/.local/bin:$PATH"' >> /etc/profile
source /etc/profile
# sudo -u efinder pip install numpy==1.22.0
cd $HOME/astrometry.net
make
make py
make extra
sudo make install
echo 'export PATH="$PATH:/usr/local/astrometry/bin"' >> /etc/profile
cd /usr/local/astrometry/data
wget http://data.astrometry.net/4100/index-4107.fits
wget http://data.astrometry.net/4100/index-4108.fits
wget http://data.astrometry.net/4100/index-4109.fits
wget http://data.astrometry.net/4100/index-4110.fits
wget http://data.astrometry.net/4100/index-4111.fits
# Install the latest version of eFinder
cd $HOME/eFinder
sudo -u efinder /home/efinder/.local/bin/poetry install
sudo -u efinder SHELL=/bin/bash poetry shell
echo "now install the ASI/QHY drivers and when ready run the following command to test everything:"
echo "python src/eFinderVNCGui.py"
