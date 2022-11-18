#/bin/sh
sudo apt update && sudo apt upgrade
sudo apt install -y netatalk
sudo echo '[Homes]' >> /etc/netatalk/afp.conf 
sudo echo 'basedir regex = /home' >> /etc/netatalk/afp.conf  
sudo systemctl restart netatalk
sudo apt install -y python3-dev gcc cargo rustc libssl-dev # needed for poetry install
sudo apt install -y libatlas-base-dev python3-dev # needed for astropy compile
sudo apt install -y make automake gcc g++
sudo apt install -y git pip neovim
sudo apt install -y libcairo2-dev libnetpbm10-dev netpbm libpng-dev libjpeg-dev zlib1g-dev libbz2-dev swig libcfitsio-dev 
cd /home/efinder 
git clone https://github.com/dstndstn/astrometry.net.git
echo 'export PATH=/home/efinder/.local/bin:$PATH' >> /etc/profile
source /etc/profile
#curl -sSL https://install.python-poetry.org | python3 -
sudo pip install poetry
cd /home/efinder/astrometry.net
make
make py
make extra
sudo make install
export PATH=$PATH:/usr/local/astrometry/bin
cd ..
mkdir Solver
mkdir Solver/images
mkdir Solver/Stills
cd eFinder
poetry install
poetry shell
python eFinderVNCGui.py -fn -fh
