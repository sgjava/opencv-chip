#!/bin/sh
#
# Created on January 31, 2017
#
# @author: sgoldsmith
#
# Install mjpg_streamer. This script will uninstall any previous version located
# in the same build directory.
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

# Set to True if you get a white image or stream.
whitepatch="True"

# Get current directory
curdir=$(cd `dirname $0` && pwd)

# Source config file
. "$curdir"/config.sh

# stdout and stderr for commands logged
logfile="$curdir/install-mjpg-streamer.log"
rm -f $logfile

# Simple logger
log(){
	timestamp=$(date +"%m-%d-%Y %k:%M:%S")
	echo "$timestamp $1"
	echo "$timestamp $1" >> $logfile 2>&1
}

# Point to our libjpeg-turbo
export CPATH="/opt/libjpeg-turbo/include"
# ARM 32
if [ "$arch" = "armv7l" ]; then
	export LIBRARY_PATH="/opt/libjpeg-turbo/lib32"
# ARM 64
elif [ "$arch" = "aarch64" ]; then
	export LIBRARY_PATH="/opt/libjpeg-turbo/lib64"
# Not supported
else
	echo "\nNo supported architectures detected!"
	exit 1
fi

# Remove temp dir
log "Removing temp dir $tmpdir"
rm -rf "$tmpdir" >> $logfile 2>&1
mkdir -p "$tmpdir" >> $logfile 2>&1

# Uninstall mjpg-streamer if it exists
if [ -d "$buildhome/mjpg-streamer" ]; then
	log "Uninstalling mjpg-streamer"
	cd "$buildhome/mjpg-streamer" >> $logfile 2>&1
	make uninstall >> $logfile 2>&1
	log "Removing $buildhome/mjpg-streamer"
	rm -rf "$buildhome/mjpg-streamer" >> $logfile 2>&1
	log "Remove www dir"
	rm -rf /usr/local/www >> $logfile 2>&1
	log "Unlink videodev.h"
	unlink /usr/include/linux/videodev.h >> $logfile 2>&1
fi

cd "$buildhome" >> $logfile 2>&1
log "Installing mjpg-streamer dependenices..."
apt-get -y install subversion g++ pkg-config build-essential cmake imagemagick libv4l-dev >> $logfile 2>&1
log "Create symlink videodev.h -> videodev2.h"
ln -s /usr/include/linux/videodev2.h /usr/include/linux/videodev.h >> $logfile 2>&1
log "Get source from subversion"
svn co https://svn.code.sf.net/p/mjpg-streamer/code/mjpg-streamer/ mjpg-streamer >> $logfile 2>&1
cd mjpg-streamer >> $logfile 2>&1
# If whitepatch is True then patch code for white image issue
if [ "$whitepatch" = "True" ]; then
	log "Get patch"
	wget -O input_uvc_patch.txt https://www.doorpi.org/forum/attachment/33-input-uvc-patch-txt/?s=8b4f23ad598b0d2b672828153aac7aad47f7e69a >> $logfile 2>&1
	log "Apply patch"
	patch -p0 < input_uvc_patch.txt >> $logfile 2>&1
fi
log "Make..."
make -j$(getconf _NPROCESSORS_ONLN) >> $logfile 2>&1
log "Install..."
make install >> $logfile 2>&1
log "Copy www dir"
cp -R www /usr/local/www >> $logfile 2>&1

# Clean up
log "Removing $tmpdir"
rm -rf "$tmpdir" 

# Get end time
endtime=$(date "$dateformat")
endtimesec=$(date +%s)

# Show elapsed time
elapsedtimesec=$(expr $endtimesec - $starttimesec)
ds=$((elapsedtimesec % 60))
dm=$(((elapsedtimesec / 60) % 60))
dh=$((elapsedtimesec / 3600))
displaytime=$(printf "%02d:%02d:%02d" $dh $dm $ds)
log "Elapsed time: $displaytime"
