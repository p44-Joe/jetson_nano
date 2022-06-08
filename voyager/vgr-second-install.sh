#!/bin/sh

#GLOBAL
set -e #know the error location
password=$1 #store sudo pass

#COMPILE AND INSTALL OPENCV 4.5.5
chip_id=$(cat /sys/module/tegra_fuse/parameters/tegra_chip_id)
case ${chip_id} in
  "33" )  # Nano and TX1
    cuda_compute=5.3
    ;;
  "24" )  # TX2
    cuda_compute=6.2
    ;;
  "25" )  # AGX Xavier
    cuda_compute=7.2
    ;;
  * )     # default
    cuda_compute=5.3,6.2,7.2
    ;;
esac

py3_ver=$(python3 -c "import sys; print(sys.version_info[1])")

folder=${HOME}/src

echo "** Purge old opencv installation"
echo $password | sudo -S apt-get purge -y libopencv*

echo "** Install requirements"
echo $password | sudo -S apt-get install -y build-essential make cmake cmake-curses-gui git g++ pkg-config curl
echo $password | sudo -S apt-get install -y libavcodec-dev libavformat-dev libavutil-dev libswscale-dev libeigen3-dev libglew-dev libgtk2.0-dev
echo $password | sudo -S apt-get install -y libtbb2 libtbb-dev libv4l-dev v4l-utils qv4l2 v4l2ucp
echo $password | sudo -S apt-get install -y libdc1394-22-dev libxine2-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev
# sudo apt-get install -y libjasper-dev
echo $password | sudo -S apt-get install -y libjpeg8-dev libjpeg-turbo8-dev libtiff-dev libpng-dev
echo $password | sudo -S apt-get install -y libxvidcore-dev libx264-dev libgtk-3-dev
echo $password | sudo -S apt-get install -y libatlas-base-dev libopenblas-dev liblapack-dev liblapacke-dev gfortran
echo $password | sudo -S apt-get install -y qt5-default

echo $password | sudo -S apt-get install -y python3-dev python3-testresources
rm -f $folder/get-pip.py
wget https://bootstrap.pypa.io/get-pip.py -O $folder/get-pip.py
echo $password | sudo -S python3 $folder/get-pip.py
echo $password | sudo -S pip3 install protobuf
echo $password | sudo -S pip3 install -U numpy matplotlib

if [ ! -f /usr/local/cuda/include/cuda_gl_interop.h.bak ]; then
  sudo cp /usr/local/cuda/include/cuda_gl_interop.h /usr/local/cuda/include/cuda_gl_interop.h.bak
fi
sudo patch -N -r - /usr/local/cuda/include/cuda_gl_interop.h < opencv/cuda_gl_interop.h.patch && echo "** '/usr/local/cuda/include/cuda_gl_interop.h' appears to be patched already.  Continue..."

echo "** Download opencv-4.5.5"
cd $folder
if [ ! -f opencv-4.5.5.zip ]; then
  wget https://github.com/opencv/opencv/archive/4.5.5.zip -O opencv-4.5.5.zip
  wget https://github.com/opencv/opencv_contrib/archive/4.5.5.zip -O opencv_contrib.zip 
fi
if [ -d opencv-4.5.5 ]; then
  echo "** ERROR: opencv-4.5.5 directory already exists"
  exit
fi
unzip opencv-4.5.5.zip
unzip opencv_contrib.zip
mv opencv-4.5.5 opencv
mv opencv_contrib-4.5.5 opencv_contrib
cd opencv/

echo "** Building opencv..."
mkdir build
cd build/

cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local \
      -D OPENCV_EXTRA_MODULES_PATH=~/src/opencv_contrib/modules \
      -D WITH_CUDA=ON -D CUDA_ARCH_BIN=${cuda_compute} -D CUDA_ARCH_PTX="" \
      -D WITH_CUBLAS=ON -D ENABLE_FAST_MATH=ON -D CUDA_FAST_MATH=ON \
      -D ENABLE_NEON=ON -D WITH_GSTREAMER=ON -D WITH_LIBV4L=ON \
      -D EIGEN_INCLUDE_PATH=/usr/include/eigen3 \
      -D BUILD_opencv_python2=OFF -D BUILD_opencv_python3=ON \
      -D BUILD_TESTS=OFF -D BUILD_PERF_TESTS=OFF -D BUILD_EXAMPLES=OFF \
      -D WITH_QT=ON -D WITH_OPENGL=ON ..
make -j$(nproc)
echo $password | sudo -S make install
echo $password | sudo -S ldconfig

python3 -c 'import cv2; print("python3 cv2 version: %s" % cv2.__version__)'

echo "** Install opencv-4.5.5 successfully"

#COMPILE AND INSTALL OPENALPR
cd ${HOME}/src
git clone https://github.com/openalpr/openalpr.git

# Setup the build directory
cd openalpr/src
mkdir build
cd build

# setup the compile environment
cmake -DCMAKE_INSTALL_PREFIX:PATH=/usr -DCMAKE_INSTALL_SYSCONFDIR:PATH=/etc -D WITH_GPU_DETECTOR=ON ..

# compile the library
make -j4

# Install the binaries/libraries to your local system (prefix is /usr)
echo $password | sudo -S make install

# Install the Python Bindings
cd ~/src/openalpr/src/bindings/python
echo $password | sudo -S python3 setup.py install

# Copy tw.conf to /usr/share/openalpr/runtime_data/config
# echo $password | sudo -S cp ~/src/Voyager/ALPR_VID/tw.conf /usr/share/openalpr/runtime_data/config/

# Test the library
wget http://plates.openalpr.com/ea7the.jpg
alpr -c us ea7the.jpg

#Install UPS POWER MODULE
cd $folder/UPS-Power-Module-master

# enable i2c permissions
echo $password | sudo -S usermod -aG i2c $USER

# install pip and some apt dependencies
echo $password | sudo -S apt-get update
echo $password | sudo -S apt install -y python3-pil
echo $password | sudo -SH pip3 install flask

# install ups_display
echo $password | sudo -S python3 setup.py install

# install UPS_Power_Module display service
python3 -m ups_display.create_display_service
echo $password | sudo -S mv ups_display.service /etc/systemd/system/ups_display.service
echo $password | sudo -S systemctl enable ups_display
echo $password | sudo -S systemctl start ups_display


