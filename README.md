# opencv-chip
If you are interested in compiling the latest version of OpenCV for the [CHIP](https://getchip.com/pages/chip) SoC then this project will show you how. You should be experienced with flashing your CHIP and formatting a USB flash drive as ext4. It also does not hurt to know Linux and OpenCV basics.

### Requirements
* CHIP
* USB 5V/2A PSU with micro USB cable or USB cable with Dupont pins for CHG-IN.
* USB flash drive formatted as ext4
* Internet connection
* USB camera (this is only if you wish to use a camera)
    * You will need a powered USB hub if you are powering off the OTG port
    * For CHG-IN you need an OTG flash drive or an adapter for OTG to USB
    * Some USB cameras like the Logitech C270 can use 500 mA at higher FPS. If the camera pulls to many mA (640x480 >= 25 FPS with the C270) then the CHIP will shut down. This will not be a big deal for most applications.

### WARNING
I used no-limit setting on CHIP to prevent power issues with OpenCV failing to compile at maximum CPU speed or with a USB drive attached. This setting could damage a laptop or PC USB port, so make sure you use a dedicated 5V/2A PSU to power off the OTG port.

### Flash CHIP
I used the [Headless 4.4](https://bbs.nextthing.co/t/chip-os-4-4-released-vga-hdmi-and-more/4319) since OpenCV compile and runtime can use quite a bit of memory. Plus all of my CV projects only require a headless server to run. After you flash your CHIP unplug everything and insert a ext4 formatted USB drive and the PSU. Boot up CHIP and ssh in (I had to ping the IP first in order for ssh to work).

* Set a static IP address
    * Activate wifi connection
         * `sudo nmtui`
    * Edit and make static address
         * `sudo nmtui`
    * Shutdown
         * `sudo shutdown now -h`

### Configure OS
* Assign hostname and IP
    * `sudo nano /etc/hostname`
    * `sudo nano /etc/hosts`
* No power limit (for OTG power only, read warning above)
    * `sudo systemctl enable no-limit`
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
         * Remove `sync` and `noexec` from MOUNTOPTIONS
    * `sudo reboot`
* Set USB drive owner
    * `sudo chown -R chip:chip /media/usb0`

### Configure and Test Camera
If you plan on processing only video or image files then you can skip this section. Live video will allow you to create smart camera applications that react to a live video stream (versus a streaming only camera). You will need to select a USB camera that works under [Linux](http://elinux.org/RPi_USB_Webcams) and has the proper resolution. Typically with the low powered SoCs you will need to limit resolutions to 640x480 or 320x240 depending on the CV application.

I will cover performance of both YUYV and MJPEG USB cameras later on. Make sure you plugged in your USB drive to the USB adapter and plug that into CHIP's OTG micro USB port. The camera should be plugged into the full size USB port.
* Add chip user to video group
    * `sudo usermod -a -G video chip`
* Install uvcdynctrl
    * `sudo apt-get install uvcdynctrl v4l-utils`
* Reboot
    * `sudo reboot`
* Get camera information (using a cheap Kinobo Origami Webcam here for illustration)
    * `lsusb`
         * `Bus 003 Device 002: ID 1871:0142 Aveo Technology Corp.`
    * `uvcdynctrl -f`
         * `Pixel format: YUYV (YUYV 4:2:2; MIME type: video/x-raw-yuv)`
 
### Streaming camera
Sometimes all you need is a live video feed without further processing. This section will be what you are looking for. It also makes sense to move the UVC processing into a different Linux process or thread from the main CV code. To build and install mjpg_streamer:
* `cd /media/usb0`
* `sudo apt-get install subversion g++ pkg-config build-essential cmake libjpeg62-turbo-dev imagemagick libv4l-dev`
* `sudo ln -s /usr/include/linux/videodev2.h /usr/include/linux/videodev.h`
* `svn co https://svn.code.sf.net/p/mjpg-streamer/code/mjpg-streamer/ mjpg-streamer`
* `cd mjpg-streamer`
* `wget -O input_uvc_patch.txt https://www.doorpi.org/forum/attachment/33-input-uvc-patch-txt/?s=8b4f23ad598b0d2b672828153aac7aad47f7e69a`
* `patch -p0 < input_uvc_patch.txt`
* `make`
* `sudo make install`
* `sudo cp -R www /usr/local/www`
* `v4l2-ctl --list-formats`
    * Check Pixel Format for 'YUYV' and/or 'MJPG'
* To run mjpg-streamer with 'YUYV' only camera use
    * `mjpg_streamer -i "/usr/local/lib/input_uvc.so -y" -o "/usr/local/lib/output_http.so -w /usr/local/www"`
* To run mjpg-streamer with 'MJPG' use
    * `mjpg_streamer -i "/usr/local/lib/input_uvc.so" -o "/usr/local/lib/output_http.so -w /usr/local/www"`
* In your web browser or VLC player goto `http://yourhost:8080/?action=stream` and you should see the video stream.

#### mjpg_streamer performance
The bottom line is you need an MJPEG USB camera because CPU usage is too high using YUYV. You might as well use the YUYV camera directly with OpenCV and not convert it to MJPEG first. CHIP only has one core, so you want to use a little CPU as possible acquiring the frames. If you plan on streaming only then this might not be a big deal, but CV is CPU intensive. I used a Logitech C270 for the following tests:

YUYV 640x480 5 FPS
* `mjpg_streamer -i "/usr/local/lib/input_uvc.so -y -n -f 5 -r 640x480" -o "/usr/local/lib/output_http.so -w /usr/local/www"`
* CPU 36%
* Bitrate 675 kb/s

MJPG 640x480 5 FPS
* `mjpg_streamer -i "/usr/local/lib/input_uvc.so -n -f 5 -r 640x480" -o "/usr/local/lib/output_http.so -w /usr/local/www"`
* CPU < 1%
* Bitrate 503 kb/s

MJPG 1280x720 5 FPS
* `mjpg_streamer -i "/usr/local/lib/input_uvc.so -n -f 5 -r 640x480" -o "/usr/local/lib/output_http.so -w /usr/local/www"`
* CPU < 1%
* Bitrate 1689 kb/s

### Build OpenCV
My OpenCV script works fine on Debian even though it was originally built and tested on Ubuntu. You will have to do a few edits on the script in order for it to work on the CHIP. TBB does not build from source right now. I need to track down why. This is fine because OpenCV will use built in TBB. The build will take about 5.5 hours.
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
