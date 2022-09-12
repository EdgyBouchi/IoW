#!/bin/bash

echo "starting patching script"
sudo apt-get install -y
sudo apt-get install network-manager -y
sudo apt-get install tmux -y
sudo nmcli con add type wifi ifname wlan0 con-name Hostspot autoconnect yes ssid Hostspot
sudo apt purge openresolv dhcpcd5 -y

echo "restarting network manager service"
sudo systemctl restart systemd-networkd

#enable i2C
sudo raspi-config nonint do_i2c 0

echo "cloning repos"
cd ~
cd ./Documents
git clone -b test https://github.com/EdgyBouchi/IoW.git
cd ~
git clone https://github.com/Seeed-Studio/grove.py
cd grove.py/ 

echo "pip installs"
sudo pip3 install .
cd ~
sudo pip3 install getmac
sudo pip3 install awscrt 
sudo pip3 install awsiotsdk  

# delete user registration file placeholder
sudo rm ./Documents/IoW/utils/captive_portal/user_register.json



echo "crontab changes for startup automation"
#write out current crontab
crontab -l > mycron
#echo new cron into cron file
#echo "@reboot python3 ./Documents/IoW/iow_launcher.py" > mycron
# '@reboot tmux new-session -d -s iow "python3 ./Documents/IoW/iow_launcher.py"' > mycron
echo "@reboot ./Documents/IoW/bootscript.sh" > mycron
echo "0 2 * * * ./Documents/IoW/crontab_pull.sh" >> mycron
#install new cron file
crontab mycron
sudo rm mycron

echo "patching script complete"
echo "patching script complete"
echo "patching script complete"