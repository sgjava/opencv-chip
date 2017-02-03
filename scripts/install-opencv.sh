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

# Oracle JDK
javahome=/usr/lib/jvm/jdk1.8.0

# Patch OpenCV Java code to fix memory leaks and performance issues.
# See https://github.com/sgjava/opencvmem for details
patchjava="False"

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

# Remove temp dir
log "Removing temp dir $tmpdir"
rm -rf "$tmpdir" >> $logfile 2>&1
mkdir -p "$tmpdir" >> $logfile 2>&1

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
log "Cloning opencv..."
git clone --depth 1 https://github.com/Itseez/opencv.git >> $logfile 2>&1
log "Cloning opencv_contrib..."
git clone --depth 1 https://github.com/Itseez/opencv_contrib.git >> $logfile 2>&1

# Patch source pre cmake
log "Patching source pre cmake"

# Patch gen_java.py to generate constants by removing from const_ignore_list
sed -i 's/\"CV_CAP_PROP_FPS\",/'\#\"CV_CAP_PROP_FPS\",'/g' "$opencvhome/modules/java/generator/gen_java.py"
sed -i 's/\"CV_CAP_PROP_FOURCC\",/'\#\"CV_CAP_PROP_FOURCC\",'/g' "$opencvhome/modules/java/generator/gen_java.py"
sed -i 's/\"CV_CAP_PROP_FRAME_COUNT\",/'\#\"CV_CAP_PROP_FRAME_COUNT\",'/g' "$opencvhome/modules/java/generator/gen_java.py"

# If patchjava is True then install OpenCV's contrib package
if [ "$patchjava" = "True" ]; then
	# Patch source pre cmake
	log "Patching Java source pre cmake"

	# Patch gen_java.py to generate nativeObj as not final, so it can be modified by free() method
	sed -i ':a;N;$!ba;s/protected final long nativeObj/protected long nativeObj/g' "$opencvhome/modules/java/generator/gen_java.py"

	# Patch gen_java.py to generate free() instead of finalize() methods
	sed -i ':a;N;$!ba;s/@Override\n    protected void finalize() throws Throwable {\n        delete(nativeObj);\n    }/public void free() {\n        if (nativeObj != 0) {\n            delete(nativeObj);\n            nativeObj = 0;\n        }    \n    }/g' "$opencvhome/modules/java/generator/gen_java.py"

	# Patch gen_java.py to generate Mat.free() instead of Mat.release() methods
	sed -i 's/mat.release()/mat.free()/g' "$opencvhome/modules/java/generator/gen_java.py"

	# Patch core+Mat.java remove final fron nativeObj, so new free() method can change
	sed -i 's~public final long nativeObj~public long nativeObj~g' "$opencvhome/modules/core/misc/java/src/java/core+Mat.java"

	# Patch core+Mat.java to replace finalize() with free() method
	sed -i ':a;N;$!ba;s/@Override\n    protected void finalize() throws Throwable {\n        n_delete(nativeObj);\n        super.finalize();\n    }/public void free() {\n        if (nativeObj != 0) {\n            release();\n            n_delete(nativeObj);\n            nativeObj = 0;\n        }    \n    }/g' "$opencvhome/modules/core/misc/java/src/java/core+Mat.java"

	# Patch utils+Converters.java to replace mi.release() with mi.free()
	sed -i 's/mi.release()/mi.free()/g' "$opencvhome$converters"
fi

# Compile OpenCV
log "Compile OpenCV..."
# Make sure root picks up JAVA_HOME for this process
export JAVA_HOME=$javahome
log "JAVA_HOME = $JAVA_HOME"
cd "$opencvhome"
mkdir build
cd build
# Optimize for CHIP
extra_c_flag="-march=armv7-a -mtune=cortex-a8 -mfpu=neon -mfloat-abi=hard"
log "Patch OpenCVCompilerOptions.cmake to apply cflags"
sed -e "/set(OPENCV_EXTRA_C_FLAGS \"\")/c\set(OPENCV_EXTRA_C_FLAGS \"${extra_c_flag}\")" -i "$opencvhome/cmake/OpenCVCompilerOptions.cmake"
sed -e "/set(OPENCV_EXTRA_CXX_FLAGS \"\")/c\set(OPENCV_EXTRA_CXX_FLAGS \"${extra_c_flag}\")" -i "$opencvhome/cmake/OpenCVCompilerOptions.cmake"
export CFLAGS="$extra_c_flag"
export CXXFLAGS="$extra_c_flag"
log "CMake..."
# Make any required changes here like if you want to build for GUI, examples, etc.
cmake $contribhome -DCMAKE_BUILD_TYPE=RELEASE -DCMAKE_INSTALL_PREFIX=/usr/local -DEXTRA_C_FLAGS=$extra_c_flag -DEXTRA_CXX_FLAGS=$extra_c_flag -DBUILD_EXAMPLES=OFF -DBUILD_TESTS=OFF -DBUILD_PERF_TESTS=OFF -DWITH_QT=OFF -DWITH_GTK=OFF -DWITH_TBB=ON -DBUILD_TBB=OFF -DENABLE_NEON=ON -DWITH_JPEG=ON -DBUILD_JPEG=OFF -DJPEG_INCLUDE_DIR=/opt/libjpeg-turbo/include -DJPEG_LIBRARY=/opt/libjpeg-turbo/lib32/libjpeg.a .. >> $logfile 2>&1
log "Make..."
make -j$(getconf _NPROCESSORS_ONLN) >> $logfile 2>&1
make install >> $logfile 2>&1
echo "/usr/local/lib" > /etc/ld.so.conf.d/opencv.conf
ldconfig >> $logfile 2>&1

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
