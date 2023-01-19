
SWAPSIZE=$(grep SwapTotal /proc/meminfo  | tr -dc '0-9')

if [ "$SWAPSIZE" -lt 1000000 ] # if less then 1G swap, enlarge
then
        echo "swapsize $SWAPSIZE: enlarging swap"
        #sudo dphys-swapfile swapoff
        #CONF_SWAPSIZE=2048
        #sudo dphys-swapfile setup
        #sudo dphys-swapfile swapon
        #sudo shutdown -r now
else
        echo "swapsize $SWAPSIZE: doing nothing"
fi