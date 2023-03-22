#!/bin/bash

echo "starting patching script"
# This was updated

cd ~
cd ./Documents/IoW
git config pull.rebase true
git pull

sleep 60

bash ./enlargeSwap.sh

FILE=./forceReboot1
if [ ! -f "$FILE" ]; then
  touch $FILE
  sudo reboot
fi

tmux send-keys -t iow C-c
sleep(5)
tmux send-keys -t iow "sudo python3 Documents/IoW/iow_launcher.py" Enter
