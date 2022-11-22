#!/bin/bash

echo "starting patching script"


cd ~
cd ./Documents/IoW
git config pull.rebase true
git pull