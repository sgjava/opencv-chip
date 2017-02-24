#!/bin/sh
#
# Created on February 21, 2017
#
# @author: sgoldsmith
#
# Make sure you change this before running any script!
#
# Tested configs:
#
# OpenCV 3.2 detects NEON, so we leave that out
#
# CHIP R8 - TBB build failed, so we use built in one
#
# extracflag="-mtune=cortex-a8 -mfloat-abi=hard"
# cmakeopts="-DBUILD_EXAMPLES=OFF -DBUILD_TESTS=OFF -DBUILD_PERF_TESTS=OFF -DWITH_QT=OFF -DWITH_GTK=OFF -DWITH_TBB=ON -DBUILD_TBB=OFF -DENABLE_NEON=ON"
#
# Pine64 - Carotene fails with "conflicts with asm clobber list", so we disable
#
# extra_c_flag="-mtune=cortex-a53"
# cmakeopts="-DBUILD_EXAMPLES=OFF -DBUILD_TESTS=OFF -DBUILD_PERF_TESTS=OFF -DWITH_QT=OFF -DWITH_GTK=OFF -DWITH_TBB=ON -DBUILD_TBB=ON -DWITH_CAROTENE=OFF"
#
# Steven P. Goldsmith
# sgjava@gmail.com
# 

# Get architecture
arch=$(uname -m)

# Temp dir for downloads, etc.
tmpdir="/media/usb0/temp"

# Build home
buildhome="/media/usb0"

# OpenCV extra cflags
extracflag="-mtune=cortex-a8 -mfloat-abi=hard"

# Custom cmake options
cmakeopts="-DBUILD_EXAMPLES=OFF -DBUILD_TESTS=OFF -DBUILD_PERF_TESTS=OFF -DWITH_QT=OFF -DWITH_GTK=OFF -DWITH_TBB=ON -DBUILD_TBB=OFF -DENABLE_NEON=ON"
