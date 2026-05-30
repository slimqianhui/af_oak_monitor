#!/bin/bash

# OAK Monitor Cron Script
export SENDER_EMAIL="qianhuirong320@gmail.com"
export SENDER_PASSWORD="ylzo lkvl vhek xiti"
export RECEIVER_EMAIL="rongqianhui@gmail.com"

cd /Users/qhrong/Documents/VS\ Code/af_oak_monitor
source ../venv/bin/activate
python oak_monitor.py >> oak_monitor.log 2>&1
