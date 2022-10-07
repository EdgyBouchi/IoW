# README #
# installation/patching


ctr alt t for terminal -> ifconfig for ip
ssh pi@ xxxxxxxxxxxx
ww raspberry


excecute 

git clone -b main https://github.com/EdgyBouchi/IoW.git 

in the ./Documents directory

* execute ./install.sh
* should install all necessary files
* reboot after script => hotspot is setup upon reboot
* after filling in network info reboot again to startup service
* crontab job should check for new code every day at 02am via a git pull

## how to acces terminal
* crontab starts a tmux session
* all services run in this tmux session
* to acces it run the following command:
* tmux attach-session -t iow
* to leave use keys ctrl+b then D to detach
* ctrl+b then X to delete session if necessary

## portal
connect to wifi network iow-device
ww iowiowiow
got to 10.42.0.1/
fill in wifi settings
should reboot
sudo reboot now if error on sensors

