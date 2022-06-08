#!/bin/sh

#GLOBAL
set -e #know the error location
password=$1 #store sudo pass
 
# INITIAL PREPARATION
echo $password | sudo -S apt update
echo $password | sudo -S apt install ssh -y
echo $password | sudo -S apt upgrade -y
echo $password | sudo -S apt-get install libopencv-dev libtesseract-dev git cmake build-essential libleptonica-dev liblog4cplus-dev libcurl3-dev beanstalkd nano mosh python3-pip zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev libbz2-dev p7zip python3-serial minicom Jetson.GPIO -y
mkdir ${HOME}/src
cd ${HOME}/src
git clone https://github.com/jkjung-avt/jetson_nano.git
cd jetson_nano/
./install_basics.sh

#OPTIMIZE PERFORMANCE
echo $password | sudo -S nvpmodel -m 0
echo $password | sudo -S jetson_clocks
echo $password | sudo -S fallocate -l 8G /mnt/8GB.swap
echo $password | sudo -S mkswap /mnt/8GB.swap
echo $password | sudo -S swapon /mnt/8GB.swap

#COMPILE LATEST PYTHON
cd ${HOME}/src
wget https://www.python.org/ftp/python/3.10.4/Python-3.10.4.tgz
tar xzvf Python-3.10.4.tgz
cd Python-3.10.4/
mkdir build 
cd build
../configure --enable-optimizations

make -j $(nproc)
echo $password | sudo -SH make install

echo $password | sudo -SH pip3 install pyserial
echo $password | sudo -SH pip3 install -U jetson-stats
echo $password | sudo -SH pip3 install smbus
echo $password | sudo -SH pip3 install Jetson.GPIO

sudo reboot
