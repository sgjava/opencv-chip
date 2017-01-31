#!/bin/sh
#
# Created on January 31, 2017
#
# @author: sgoldsmith
#
# Install mjpg_streamer
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

# stdout and stderr for commands logged
logfile="$curdir/install-mjpg-streamer.log"
rm -f $logfile

# Simple logger
log(){
	timestamp=$(date +"%m-%d-%Y %k:%M:%S")
	echo "$timestamp $1"
	echo "$timestamp $1" >> $logfile 2>&1
}

# Uninstall mjpg-streamer if it exists
if [ -d "$buildhome/mjpg-streamer" ]; then
	log "Uninstalling mjpg-streamer"
	cd "$buildhome/mjpg-streamer" >> $logfile 2>&1
	make uninstall >> $logfile 2>&1
	log "Removing $buildhome/mjpg-streamer"
	rm -rf "$buildhome/mjpg-streamer" >> $logfile 2>&1
	log "Unlink videodev.h"
	unlink /usr/include/linux/videodev.h >> $logfile 2>&1
fi

cd "$buildhome" >> $logfile 2>&1
log "Installing mjpg-streamer dependenices..."
apt-get -y install subversion g++ pkg-config build-essential cmake libjpeg62-turbo-dev imagemagick libv4l-dev >> $logfile 2>&1
log "Create symlink videodev.h -> videodev2.h"
ln -s /usr/include/linux/videodev2.h /usr/include/linux/videodev.h >> $logfile 2>&1
log "Get source from subversion"
svn co https://svn.code.sf.net/p/mjpg-streamer/code/mjpg-streamer/ mjpg-streamer >> $logfile 2>&1
cd mjpg-streamer >> $logfile 2>&1
log "Get patch"
wget -O input_uvc_patch.txt https://www.doorpi.org/forum/attachment/33-input-uvc-patch-txt/?s=8b4f23ad598b0d2b672828153aac7aad47f7e69a >> $logfile 2>&1
log "Apply patch"
patch -p0 < input_uvc_patch.txt >> $logfile 2>&1
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

# Show elapse time
elapsedtimesec=$(expr $endtimesec - $starttimesec)
ds=$((elapsedtimesec % 60))
dm=$(((elapsedtimesec / 60) % 60))
dh=$((elapsedtimesec / 3600))
displaytime=$(printf "%02d:%02d:%02d" $dh $dm $ds)
log "Elapsed time: $displaytime"
