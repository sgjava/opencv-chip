#!/bin/sh
#
# Created on January 31, 2017
#
# @author: sgoldsmith
#
# Install OpenCV
#
# This should work on other ARM based systems with similar architecture and
# Ubuntu as well.
#
# Steven P. Goldsmith
# sgjava@gmail.com
# 

# Get start time
dateformat="+%a %b %-eth %Y %I:%M:%S %p %Z"
starttime=$(date "$dateformat")
starttimesec=$(date +%s)

# Get current directory
curdir=$(cd `dirname $0` && pwd)

# Temp dir for downloads, etc.
tmpdir="/media/usb0/temp"

# Build home
buildhome="/media/usb0"
opencvhome="$buildhome/opencv"
contribhome="$buildhome/opencv_contrib"

# stdout and stderr for commands logged
logfile="$curdir/install-opencv.log"
rm -f $logfile

# Simple logger
log(){
	timestamp=$(date +"%m-%d-%Y %k:%M:%S")
	echo "$timestamp $1"
	echo "$timestamp $1" >> $logfile 2>&1
}

# Uninstall OpenCV if it exists
if [ -d "$opencvhome" ]; then
	log "Uninstalling OpenCV"
	cd "$opencvhome/build" >> $logfile 2>&1
	make uninstall >> $logfile 2>&1
	log "Removing $opencvhome"
	rm -rf "$opencvhome" >> $logfile 2>&1
	log "Removing $contribhome"
	rm -rf "$contribhome" >> $logfile 2>&1
fi

log "Installing OpenCV dependenices..."
# Install build tools
apt-get -y install build-essential pkg-config cmake yasm doxygen >> $logfile 2>&1

# Install media I/O libraries 
apt-get -y install libjpeg62-turbo-dev libpng-dev libtiff5-dev >> $logfile 2>&1

# Install video I/O libraries, support for Firewire video cameras and video streaming libraries
apt-get -y install libdc1394-22-dev libavcodec-dev libavformat-dev libswscale-dev libavresample-dev libx264-dev libv4l-dev >> $logfile 2>&1

# Install the Python development environment and the Python Numerical library
apt-get -y install python-dev python-numpy python3-dev python3-numpy >> $logfile 2>&1

# Install the parallel code processing and linear algebra library
apt-get -y install opencl-headers libtbb2 libtbb-dev libeigen3-dev libatlas-dev libatlas3gf-base libatlas-base-dev >> $logfile 2>&1

cd "$buildhome" >> $logfile 2>&1
log "Cloning opencv"
git clone --depth 1 git clone --depth 1 https://github.com/Itseez/opencv.git >> $logfile 2>&1
log "Cloning opencv_contrib"
git clone --depth 1 https://github.com/Itseez/opencv_contrib.git >> $logfile 2>&1

# Compile OpenCV
log "Compile OpenCV..."
cd "$opencvhome"
mkdir build
cd build
extra_c_flag="-march=armv7-a -mtune=cortex-a8 -mfpu=neon -mfloat-abi=hard"
log "Apply cflags in opencvCompilerOptions

#cmake \$opencvextramodpath -DCMAKE_BUILD_TYPE=RELEASE -DCMAKE_INSTALL_PREFIX=/usr/local -DWITH_QT=OFF -DWITH_TBB=ON -DBUILD_TBB=ON -DBUILD_EXAMPLES=ON -DBUILD_TESTS=OFF -DBUILD_PERF_TESTS=OFF -DBUILD_JPEG=ON -DENABLE_VFPV3=ON -DENABLE_NEON=ON .. >> $logfile 2>&1

# Clean up
log "Removing $tmpdir"
rm -rf "$tmpdir" 

# Get end time
endtime=$(date "$dateformat")
endtimesec=$(date +%s)

# Show elapse time
elapsedtimesec=$(expr $endtimesec - $starttimesec)
ds=$((elapsedtimesec % 60))
dm=$(((elapsedtimesec / 60) % 60))
dh=$((elapsedtimesec / 3600))
displaytime=$(printf "%02d:%02d:%02d" $dh $dm $ds)
log "Elapsed time: $displaytime"
