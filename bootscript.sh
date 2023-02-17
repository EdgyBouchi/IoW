#!/bin/bash
sleep 60
tmux new-session -d -s iow 
tmux send-keys -t 0 "sudo python3 Documents/IoW/iow_launcher.py" Enter