#!/bin/bash
sleep 1
service plymouth stop
service plymouth-start stop
llxup='/sbin/lliurex-up -u -s -n'
xinit $llxup $* -- :0 vt$XDG_VTNR &
sleep 5
service plymouth stop
service plymouth-start stop
chvt $XDG_VTNR
while [ ! -e /tmp/.updateEnd ] 
do
	echo "WAIT"
	sleep 10
done
kdialog --title "Lliurex Release Upgrade" --msgbox "Press to reboot" && reboot
