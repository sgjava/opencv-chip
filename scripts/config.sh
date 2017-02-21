#!/bin/sh
#
# Created on February 21, 2017
#
# @author: sgoldsmith
#
# Make sure you change this before running any script!
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

# Optimize for CHIP R8. OpenCV 3.2 auto detects NEON, so we leave that out
#extracflag="-mtune=cortex-a8 -mfloat-abi=hard"

# Leaving default since libjpeg-turbo and OpenCV detect CPU features
extracflag=""