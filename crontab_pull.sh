#!/bin/bash

echo "starting patching script"


cd ~
cd ./Documents/IoW
git config pull.rebase true
git pull

sleep 60

FILE=./forceReboot1
if [ ! -f "$FILE" ]; then
  touch $FILE
  sudo reboot
fi