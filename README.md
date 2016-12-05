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
    