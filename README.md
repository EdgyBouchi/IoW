# README #
# installation/patching


on raspberry pi itself:

  ctr alt t for terminal -> ifconfig      for ip
  
on your device:

  ssh pi@ xx.xx.xx.xx.
  ww: raspberry

  change directory to documents:
  
     cd Documents
  
  
  excecute 

     git clone -b main https://github.com/EdgyBouchi/IoW.git 

* execute ./install.sh
* should install all necessary files
* reboot after script => hotspot is setup upon reboot

## portal
 * connect to wifi network iow-device
 * ww: iowiowiow
 * go to 10.42.0.1/
 * fill in wifi settings hotspot/wifi network
 * should reboot after 30 or so sec

## Checking sensors
* crontab starts a tmux session
* all services run in this tmux session
* to acces it run the following command:

      tmux attach-session -t iow
      
* to leave use keys ctrl+b then D to detach
* ctrl+b then X to delete session if necessary(also kills services currently running)
* tmux session is started after 60 seconds so you need to wait a bit after rebooting
* Sensors should be logging data and writing them away(should see sensor values + queue)
* if all sensors are working:

      rm -rf Documents/IoW/utils/captive_portal/user_register.json
* safe shutdown    
    
      sudo shutdown now 

## rebooting

        sudo reboot now
   
## crontab job should check for new code every day at 02am via a git pull
