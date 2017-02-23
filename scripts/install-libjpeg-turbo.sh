#!/bin/sh
#
# Created on January 31, 2017
#
# @author: sgoldsmith
#
# Install libjpeg-turbo. This script will uninstall any previous version located
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

# Get current directory
curdir=$(cd `dirname $0` && pwd)

# Source config file
. "$curdir"/config.sh

# Fix "final link failed: Bad value" in OpenCV build
export CFLAGS="-fPIC -O3"
export CXXFLAGS="-fPIC -O3"

# stdout and stderr for commands logged
logfile="$curdir/install-libjpeg-turbo.log"
rm -f $logfile

# Simple logger
log(){
	timestamp=$(date +"%m-%d-%Y %k:%M:%S")
	echo "$timestamp $1"
	echo "$timestamp $1" >> $logfile 2>&1
}

# Remove temp dir
log "Removing temp dir $tmpdir"
rm -rf "$tmpdir" >> $logfile 2>&1
mkdir -p "$tmpdir" >> $logfile 2>&1

# Uninstall libjpeg-turbo if it exists
if [ -d "$buildhome/libjpeg-turbo" ]; then
	log "Uninstalling libjpeg-turbo"
	cd "$buildhome/libjpeg-turbo/build" >> $logfile 2>&1
	make uninstall >> $logfile 2>&1
	log "Removing $buildhome/libjpeg-turbo"
	rm -rf "$buildhome/libjpeg-turbo" >> $logfile 2>&1
fi

cd "$buildhome" >> $logfile 2>&1
log "Installing libjpeg-turbo dependenices..."
apt-get -y install dh-autoreconf g++ pkg-config build-essential yasm >> $logfile 2>&1
log "Cloning libjpeg-turbo"
git clone --depth 1 https://github.com/libjpeg-turbo/libjpeg-turbo.git >> $logfile 2>&1
# Patch source pre cmake
log "Patching source pre compile"
# Patch jdhuff.c to remove "Invalid SOS parameters for sequential JPEG" warning
sed -i 's~WARNMS(cinfo, JWRN_NOT_SEQUENTIAL);~//WARNMS(cinfo, JWRN_NOT_SEQUENTIAL);\n      ; // NOP~g' "$buildhome/libjpeg-turbo/jdhuff.c" >> $logfile 2>&1
# Patch jdmarker.c to remove "Corrupt JPEG data: xx extraneous bytes before marker 0xd9" warning
sed -i 's~WARNMS2(cinfo, JWRN_EXTRANEOUS_DATA~//WARNMS2(cinfo, JWRN_EXTRANEOUS_DATA~g' "$buildhome/libjpeg-turbo/jdmarker.c" >> $logfile 2>&1
cd libjpeg-turbo >> $logfile 2>&1
mkdir build >> $logfile 2>&1
log "autoreconf"
autoreconf -fiv >> $logfile 2>&1
cd build >> $logfile 2>&1
log "Configure..."
sh ../configure >> $logfile 2>&1
log "Make..."
make -j$(getconf _NPROCESSORS_ONLN) >> $logfile 2>&1
log "Install..."
make install >> $logfile 2>&1

# ARM 64
if [ "$arch" = "aarch64" ]; then
	# See if LD_LIBRARY_PATH exists and if not add it to /etc/environment
	if grep -q "LD_LIBRARY_PATH" /etc/environment; then
		log "LD_LIBRARY_PATH already exists"
	else
		# Add LD_LIBRARY_PATH to /etc/environment
		log "Adding LD_LIBRARY_PATH to /etc/environment"
		echo "LD_LIBRARY_PATH=/opt/libjpeg-turbo/lib64" >> /etc/environment
		. /etc/environment
	fi
fi

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
