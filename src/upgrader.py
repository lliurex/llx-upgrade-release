#!/bin/bash
mount -o remount,defaults,nodelalloc /

LLXUP_TOKEN="/var/run/disableMetaProtection.token"
UPGRADER="/usr/share/llx-upgrade-release/qupgrader.py"
touch $LLXUP_TOKEN
xinit $UPGRADER $* -- :0 vt1 
