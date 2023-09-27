#!/bin/bash
mount -o remount,defaults,nodelalloc /

LLXUP_TOKEN="/var/run/disableMetaProtection.token"
UPGRADER="/usr/share/llx-upgrade-release/bkgfixer.py"

error()
{
	kdialog --title "Lliurex Release Upgrade" --msgbox "Upgrade ended with errors.<br>A terminal will be executed. Don't reboot till the system gets fixed"
	konsole || xterm
}

touch $LLXUP_TOKEN
xinit $UPGRADER $* -- :0 vt1 &
