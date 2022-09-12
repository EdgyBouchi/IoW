# IoW script to install all prerequisites
echo "starting install script"

sudo systemctl enable ssh
sudo systemctl start ssh


sudo apt-get install -y
sudo apt-get install network-manager -y
sudo apt-get install tmux -y
sudo nmcli con add type wifi ifname wlan0 con-name Hostspot autoconnect yes ssid Hostspot
sudo apt purge openresolv dhcpcd5 -y


#enable i2C
sudo raspi-config nonint do_i2c 0

#clone repos
echo "cloning repos"
cd ~
cd ./Documents
git clone -b main https://github.com/EdgyBouchi/IoW.git
cd ~
git clone https://github.com/Seeed-Studio/grove.py
cd grove.py/ 
cd grove.py/ 
echo "pip installs grove"
sudo pip3 install .

echo "requirements.txt"
cd ~
cd IoW
pip install -r requirements.txt

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