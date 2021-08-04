#!/bin/bash
# Give it some time to make sure everything is loaded
sleep 5

# Switching working directory
cd /home/ubuntu/environments/src

# Activate environment and then run 
source /home/ubuntu/environments/my_env/bin/activate
python3 /home/ubuntu/environments/src/franklin.py
