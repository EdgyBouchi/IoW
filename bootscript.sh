#!/bin/bash
tmux new-session -d -s iow 
tmux send-keys -t 0 "python3 ./iow_launcher.py" Enter