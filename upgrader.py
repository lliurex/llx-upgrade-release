#!/bin/bash
Xdummy :0 &
export DISPLAY=:0
sleep 3
echo .....
DISPLAY=:0 lliurex-up -u -s -m
