# opencv-chip
If you are interested in compiling the latest version of OpenCV for the [CHIP](https://getchip.com/pages/chip) SoC then this project will show you how. You should be experienced with flashing your CHIP and formatting a USB drive as ext4. It also does not hurt to know Linux and OpenCV basics.

### Requirements
* CHIP
* 5V/2A PSU with micro USB connection
* USB drive formatted as ext4
* Internet connection
* USB camera and micro USB male to USB female adapter (this is only if you wish to use a camera)

### WARNING
I used nolimit setting on CHIP to prevent power issues with OpenCV failing to compile at maximum CPU speed or with a USB drive attached. This setting could damage a laptop or PC USB port, so make sure you use a dedicated 5V/2A PSU. I'm testing with CHG-IN with 5V/2A PSU as well.

### Flash CHIP
I used the [Headless 4.4](https://bbs.nextthing.co/t/chip-os-4-4-released-vga-hdmi-and-more/4319) since OpenCV compile and runtime can use quite a bit of memory. Plus all of my CV projects only require a headless server to run. After you flash your CHIP unplug everything and insert a ext4 formatted USB drive and the PSU. Boot up CHIP and ssh in (I had to ping the IP first in order for ssh to work).

* Set a static IP address
    * `sudo nmtui` (activate wifi connection)
    * `sudo nmtui` (edit and make static address)
    * `sudo shutdown now -h`

### Configure OS
* Assign hostname and IP
    * `sudo nano /etc/hostname`
    * `sudo nano /etc/hosts`
* No power limit (read warning above)
    * `sudo nano /etc/crontab`
         * `@reboot root /usr/sbin/i2cset -y -f 0 0x34 0x30 0x63`
    * `sudo reboot`
* Do updates
    * `sudo apt-get update`
    * `sudo apt-get upgrade`
* Configure locales and timezone
    * `sudo apt-get install locales`
    * `sudo dpkg-reconfigure locales`
    * `sudo dpkg-reconfigure tzdata`
* Auto mount USB drive
    * `sudo apt-get install usbmount`
    * `sudo nano /etc/usbmount/usbmount.conf`
         * Remove sync, from MOUNTOPTIONS
    * `sudo reboot`
* Set USB drive owner
    * `sudo chown -R chip:chip /media/usb0`

### Configure and Test Camera
If you plan on processing only video or image files then you can skip this section. Live video will allow you to create smart camera applications that react to a live video stream (versus a dumb streaming camera). You will need to select a USB camera that works under [Linux](http://elinux.org/RPi_USB_Webcams) and has the proper resolution. Typically with the low powered SoCs you will need to limit resolutions to 640x480 or 320x240 depending on the application. A less than $10 camera may be just fine for some applications.

I will cover performance of both YUYV and MJPEG USB cameras later on. Make sure you plugged in your camera to the USB adapter and plug that into CHIP's OTG micro USB port.
* Add chip user to video group
    * `sudo usermod -a -G video chip`
* Install uvcdynctrl
    * `sudo apt-get install uvcdynctrl`
* Reboot
    * `sudo reboot`
* Get camera information (using a cheap Kinobo Origami Webcam here for illustration)
    * `lsusb`
    ```
Bus 003 Device 002: ID 1871:0142 Aveo Technology Corp.
    ```
    * `uvcdynctrl -f`
    ```
Listing available frame formats for device video0:
Pixel format: YUYV (YUYV 4:2:2; MIME type: video/x-raw-yuv)
  Frame size: 640x480
    Frame rates: 30
  Frame size: 160x120
    Frame rates: 30
  Frame size: 320x240
    Frame rates: 30
  Frame size: 176x144
    Frame rates: 30
  Frame size: 352x288
    Frame rates: 30
    ```

### Build OpenCV
My OpenCV script works fine on Debian even though it was originally built and tested on Ubuntu. You will have to do a few edits on the script in order for it to work on the CHIP. TBB does not build from source right now. I need to track down why. This is fine because OpenCV will use built in TBB.
* Install Git client
    * `sudo apt-get install git-core`
* On ARM platforms with limited memory create a swap file or the build may fail
with an out of memory exception. To create a 512MB swap file use:
    * `sudo su -`
    * `cd /media/usb0`
    * `dd if=/dev/zero of=tmpswap bs=512 count=1M`
    * `chmod 0600 tmpswap`
    * `mkswap tmpswap`
    * `swapon tmpswap`
    * `free`
    * `exit`
* `cd /media/usb0`
* `git clone --depth 1 https://github.com/sgjava/install-opencv.git`
* `cd install-opencv/scripts/ubuntu`
* `nano config-install.sh`
    * Change $HOME to /media/usb0
* `nano install-opencv.sh`
    * Change -DBUILD_TBB=ON to -DBUILD_TBB=OFF
* Run individual scripts to update individual components
    * `sudo sh install-java.sh` to install/update Java
    * `sudo sh install-opencv.sh` to install/update OpenCV
* Run script in foreground or background to install all components
    * `sudo sh install.sh` to run script in foreground
    * `sudo nohup sh install.sh &` to run script in background


  
    