# FROM balenalib/raspberry-pi-debian:latest
# using 64 bit debian to avoid https://github.com/JonasAlfredsson/docker-nginx-certbot/issues/109 
FROM balenalib/raspberrypi4-64-debian:latest
# Fix for the core dump on mac M1: https://github.com/balena-io-library/base-images/issues/741
ENV QEMU_CPU=max

RUN apt-get update && apt-get install -y openssl sudo git xfce4 faenza-icon-theme bash python3 tigervnc-common xfce4-terminal \
    cmake wget pulseaudio xfce4-pulseaudio-plugin pavucontrol nodejs npm
RUN git clone https://github.com/novnc/noVNC /opt/noVNC \
    && git clone https://github.com/novnc/websockify /opt/noVNC/utils/websockify \
    && wget https://raw.githubusercontent.com/novaspirit/Alpine_xfce4_noVNC/dev/script.js -O /opt/noVNC/script.js \
    && wget https://raw.githubusercontent.com/novaspirit/Alpine_xfce4_noVNC/dev/audify.js -O /opt/noVNC/audify.js \
    && wget https://raw.githubusercontent.com/novaspirit/Alpine_xfce4_noVNC/dev/vnc.html -O /opt/noVNC/index.html \
    && wget https://raw.githubusercontent.com/novaspirit/Alpine_xfce4_noVNC/dev/pcm-player.js -O /opt/noVNC/pcm-player.js
RUN npm install --prefix /opt/noVNC ws
RUN npm install --prefix /opt/noVNC audify
RUN useradd -ms /bin/bash efinder
RUN echo 'efinder:asinexus' | chpasswd
RUN adduser efinder sudo

# RUN echo -e "\n\n\n\n\n\n" | openssl req -new -x509 -days 365 -nodes -out self.pem -keyout /opt/noVNC/utils/websockify/self.pem

# RUN echo $'\0#!/bin/bash\n\
# ls .X99-lock >> /dev/null 2>&1 && rm -rf /tmp/.X99-lock & \n\
# sleep 1 \n\
# sudo mkdir -p /home/efinder/.vnc & \n\
# sleep 1 \n\
# echo "SecurityTypes=None" | sudo tee -a /home/efinder/.vnc/config \n\
# sleep 1 \n\
# echo -e "#!/bin/bash\nstartxfce4 &" | sudo tee -a /home/efinder/.vnc/xstartup & \n\
# sleep 1 \n\
# /usr/bin/vncserver :99 2>&1 | sed  "s/^/[Xtigervnc ] /" & \n\
# sleep 1 \n\
# /usr/bin/pulseaudio 2>&1 | sed  "s/^/[pulseaudio] /" & \n\
# sleep 1 \n\
# /usr/bin/node /opt/noVNC/audify.js 2>&1 | sed "s/^/[audify    ] /" & \n\
# /opt/noVNC/utils/novnc_proxy --vnc localhost:5999 2>&1 | sed "s/^/[noVNC     ] /"'\
# >/entry.sh

# USER efinder
# WORKDIR /home/efinder
# RUN mkdir /home/efinder/eFinder
# COPY . /home/efinder/eFinder
#USER root
#RUN chmod +x /home/efinder/eFinder/pi-install.sh && /home/efinder/eFinder/pi-install.sh

ENTRYPOINT ["./entry.sh"]
