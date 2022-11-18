FROM balenalib/raspberry-pi-debian:latest
# Fix for the core dump on mac M1: https://github.com/balena-io-library/base-images/issues/741
ENV QEMU_CPU=max
RUN useradd -ms /bin/bash efinder
RUN echo 'efinder:asinexus' | chpasswd
RUN adduser efinder sudo
USER efinder
WORKDIR /home/efinder


