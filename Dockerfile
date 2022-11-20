# FROM balenalib/raspberry-pi-debian:latest
# using 64 bit debian to avoid https://github.com/JonasAlfredsson/docker-nginx-certbot/issues/109 
FROM balenalib/raspberrypi4-64-debian:latest
# Fix for the core dump on mac M1: https://github.com/balena-io-library/base-images/issues/741
ENV QEMU_CPU=max
RUN useradd -ms /bin/bash efinder
RUN echo 'efinder:asinexus' | chpasswd
RUN adduser efinder sudo
USER efinder
WORKDIR /home/efinder
RUN mkdir /home/efinder/eFinder
COPY . /home/efinder/eFinder
USER root
RUN chmod +x /home/efinder/eFinder/pi-install.sh && /home/efinder/eFinder/pi-install.sh

ENTRYPOINT ["tail", "-f", "/dev/null"]
