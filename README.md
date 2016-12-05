# opencv-chip
If you are interested in compiling the latest version of OpenCV for the CHIP SoC then this project will show you how. You should be experienced with flashing your CHIP and formatting a USB drive as ext4.

### Requirements
* CHIP
* 5V/2A PSU with micro USB connection
* USB drive formatted as ext4
* Internet connection

### WARNING
I used nolimit setting on CHIP to prevent power issues with OpenCV failing to compile at maximum CPU speed or with a USB drive attached. This setting could damage a laptop or PC USB port, so make sure you use a dedicated 5V/2A PSU.

### Flash CHIP
I used the Headless 4.4 since OpenCV compile and runtime can use quite a bit of memory. Plus all of my CV projects only require a headless server to run. After you flash your CHIP unplug everything and insert a ext4 formatted USB drive and the PSU. Boot up CHIP.

* Set a static IP address
    * `sudo nmtui` (create static address)
    * `sudo shutdown now -h`

### Configure OS
* Assign hostname and IP
    * `sudo nano /etc/hostname`
    * `sudo nano /etc/hosts`
    * `sudo reboot`
* Do updates
    * `sudo apt-get update`
    * `sudo apt-get upgrade`
* Configure locales and timezone
    * `sudo apt-get install locales`
    * `sudo dpkg-reconfigure locales`
    * `sudo dpkg-reconfigure tzdata`
* No power limit
    * `sudo nano /etc/crontab`
         * `@reboot root /usr/sbin/i2cset -y -f 0 0x34 0x30 0x63`
    * `sudo reboot`
* Auto mount USB drive
    * `sudo apt-get install usbmount`
    * `sudo nano /etc/usbmount/usbmount.conf`
         * Rremove  sync, from MOUNTOPTIONS
    * `sudo reboot`
* Set USB drive owner
    * `sudo chown -R chip:chip /media/usb`
    
### Build OpenCV
My OpenCV script works fine on Debian even though it was originally built and tested on Ubuntu. You will have to do a few edits on the script in order for it to work on the CHIP.
* Install Git client
    * `sudo apt-get install git-core`
* On ARM platforms with limited memory create a swap file or the build may fail
with an out of memory exception. To create a 1GB swap file use:
    * `sudo su -`
    * `cd /media/usb`
    * `dd if=/dev/zero of=tmpswap bs=1024 count=1M`
    * `mkswap tmpswap`
    * `swapon tmpswap`
    * `free`
* `git clone --depth 1 https://github.com/sgjava/install-opencv.git`
* `cd install-opencv/scripts/ubuntu`
* Edit config-*.sh files and change versions or switches as needed
* Run individual scripts to update individual components
    * `sudo ./install-java.sh` to install/update Java
    * `sudo ./install-opencv.sh` to install/update OpenCV
* Run script in foreground or background to install all components
    * `sudo ./install.sh` to run script in foreground
    * `sudo sh -c 'nohup ./install.sh &'` to run script in background


  
    